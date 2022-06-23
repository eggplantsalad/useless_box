# useless box
# Essentially, a control flow for turning off a switch via servo with pre-selected
# patterns

# power is enabled via a switch, and parallel to that with a relay

import board_io
from log import log
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
            wait_time = abs(angle_to - angle_from) * self.servo.time_per_degree
            self.servo.set_angle(angle_to)
            time.sleep(wait_time)
            return

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

    # return a random number 0..(count-1)
    def get(self, count: int) -> int:
        self.seed ^= self.seed << 13
        self.seed ^= self.seed >> 17
        self.seed ^= self.seed << 5
        self.seed &= 0xFFFFFFFF
        return self.seed % count


servo = board_io.Servo(config.servo_time_60deg)
mover = ArmMover(servo)
rnd = Rnd()
key_list = list(patterns.keys())
nr = 0
while True:
    id = key_list[nr]
    mover.execute_pattern(id)
    log('Closed')
    if not board_io.await_switch(config.power_off_time_s):
        log('Powering off')
        board_io.power_off()
        exit()
    rnd.entropy(time.monotonic_ns())
    nr = rnd.get(len(patterns))
