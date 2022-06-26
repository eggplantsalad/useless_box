# useless box
# Essentially, a control flow for turning off a switch via servo with pre-selected
# patterns

# power is enabled via a switch, and parallel to that with a relay

import board_io
from log import log
import math
import time
import config
if config.have_typing:
    from typing import Optional
else:
    Optional = type  # type: ignore

# patterns for turning off: ID, list of {time, target angle} pairs
# time: seconds for movement. 'None': as fast as possible
# angle: 0..1 for min..max (with 1 turning off). 'None': No change
patterns: dict[str, list[tuple[Optional[float], Optional[float]]]] = {
    'simple_off': [(None, 1), (None, 0)],
    'delayed_off': [(2, None), (None, 1), (None, 0)],
    'teaser': [(1, None), (None, 0.5), (1, 0), (.5, 0.9), (2, None), (None, 1), (None, 0)],
    'shy': [(1, 0.2), (2, None), (1, 0.3), (1, None), (1, 0.5), (1, None), (1, 1), (.5, 0)],
    'wiggle': [(.5, .5), (.3, .7), (.3, .5), (.3, .7), (.3, .5), (.3, .7), (.3, .5), (.3, .7), (.3, .5), (1, 1), (.5, 0)],
    'pushpushpush': [(None, 0.8), (1, None), (0.2, 1), (0.2, 0.7), (0.2, 0.96), (0.2, 0.7), (0.2, 0.96)]
}


class ArmMover:
    def __init__(self, servo: board_io.Servo):
        self.servo = servo

    def execute_move(self, time_in_s: Optional[float], angle_from: float, angle_to: float):
        if time_in_s is None:
            # move as fast as possible: Set output angle and wait for the servo to respond
            wait_time = abs(angle_to - angle_from) * self.servo.time_per_degree * config.wait_time_multiplier
            self.servo.set_angle(angle_to)
            time.sleep(wait_time)
            return

        time_in_s *= config.wait_time_multiplier

        if angle_from == angle_to:
            # no move, wait
            time.sleep(time_in_s)
            return

        # timed move: In a tight loop, set target angle according to progressing time
        time_ns = time_in_s * 1000 * 1000 * 1000
        time_now = time.monotonic_ns()
        time_0 = time_now
        time_end = time_now + time_ns
        deg_per_ns = (angle_to - angle_from) / time_ns
        while time_now < time_end:
            deg = (time_now - time_0) * deg_per_ns
            self.servo.set_angle(angle_from + deg)
            time.sleep(.01)
            time_now = time.monotonic_ns()
        self.servo.set_angle(angle_to)

    def execute_pattern(self, name: str):
        log('Pattern: %s' % name)
        moves: list = patterns[name]
        angle_now = config.angle_off
        for m in moves:
            if m[1] is None:
                angle_tgt = angle_now
            else:
                angle_tgt = m[1] * (config.angle_max - config.angle_off) + config.angle_off
            self.execute_move(m[0], angle_now, angle_tgt)
            angle_now = angle_tgt
        self.execute_move(None, angle_now, config.angle_off)


# simple xorshift32 generator
class Rnd():
    def __init__(self):
        # using ctypes.c_uint32 is a pain-in-the-neck, why is that crap so hard
        self.seed = 1

    def entropy(self, e: int):
        self.seed = (self.seed + e) & 0xFFFFFFFF
        if self.seed == 0:
            self.seed = 1

    # return a random int 0..0xFFFFFFFF
    def get32(self) -> int:
        self.seed ^= self.seed << 13
        self.seed ^= self.seed >> 17
        self.seed ^= self.seed << 5
        self.seed &= 0xFFFFFFFF
        return self.seed

    # return a random int 0 <= result < max
    def get(self, max: int) -> int:
        return self.get32() % max

    # return a random float 0 <= result < max
    def get_float(self, max: float) -> float:
        return self.get(0xFFFFFFFF) * max / 0x100000000


# Given the historic counts of the moves, randomly pick the next pattern
# Although we could calculate the total # of moves, we can easily count it & save some time
#
# Goal: Prefer those moves that hadn't been picked often. Specifically, a move that hasn't been
# executed often is selected with higher probability.
def pick_next_move(pattern_used: list[int], moves_total: int, rnd: Rnd) -> int:
    nrs: list[tuple[int, float]] = list()
    p: float = 0
    s_2 = 0
    avg = moves_total / len(pattern_used)
    for nr, count in enumerate(pattern_used):
        chance = (avg / (count + 1)) ** 3
        s_2 += count**2
        p += chance
        log('  nr=%d (%-12s), count=%d, chance=%.3f, p=%.3f' % (nr, list(patterns.keys())[nr], count, chance, p))
        nrs.append((nr, p))

    log('s^2=%d, total^2=%d, sqrt(total^2/s^2*len)=%.3f' %
        (s_2, moves_total**2, math.sqrt((moves_total**2) / s_2 / len(pattern_used))), level=2)

    r = rnd.get_float(p)
    log('p=%.3f, r=%.3f' % (p, r), level=2)
    for idx, (nr, p) in enumerate(nrs):
        log('idx = %d, nr=%d, p=%.3f' % (idx, nr, p), level=3)
        if r <= p:
            return nr
    assert(False)
    return 0


servo = board_io.Servo(config.servo_time_60deg)
mover = ArmMover(servo)
rnd = Rnd()
key_list = list(patterns.keys())
pattern_used: list[int] = [0] * len(patterns)
moves_total = 0
nr = 0
while True:
    id = key_list[nr]
    mover.execute_pattern(id)
    moves_total += 1
    pattern_used[nr] += 1
    log('Closed')
    if not board_io.await_switch(config.power_off_time_s):
        log('Powering off')
        board_io.power_off()
        exit()

    # pick next move
    rnd.entropy(time.monotonic_ns())
    nr = pick_next_move(pattern_used, moves_total, rnd)
