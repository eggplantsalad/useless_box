import board_io_base
import config as config
from log import log
import time


if config.native:
    import digitalio
    import pwmio

    switch = digitalio.DigitalInOut(config.gpio_switch)
    switch.direction = digitalio.Direction.INPUT

    relay_out = digitalio.DigitalInOut(config.gpio_power_sel)
    relay_out.direction = digitalio.Direction.OUTPUT
    relay_out.value = 0

    # wait until switch is set w/ timeout
    # returns: True if switch is toggled in time, False otherwise
    def await_switch(time_s: float) -> bool:
        log('Waiting for switch, up to %d seconds' % time_s, level=2)
        ts_end = time.monotonic_ns() + (time_s * 1000 * 1000 * 1000)
        while not switch.value:
            log("Switch.value: %d" % switch.value, level=3)
            ts_now = time.monotonic_ns()
            if ts_now > ts_end:
                return False
            # power consumption does not differ when we sleep, so no reason to delay here
        return True

    def power_off():
        # raise level, though this might not be enough. So, also configure to input
        relay_out.value = 1
        relay_out.direction = digitalio.Direction.INPUT

    class Servo(board_io_base.ServoBase):
        def __init__(self, time_60_deg: float, freq=100, t_0_ms=0.5, t_180_ms=2.5):
            super().__init__(time_60_deg)
            self.pwm = pwmio.PWMOut(config.gpio_servo, frequency=freq, duty_cycle=0)
            self.freq = freq
            self.t_0_ms = t_0_ms
            self.t_180_ms = t_180_ms
            self.t_deg_ms = (t_180_ms - t_0_ms) / 180

        def pwmduty_ms(self, t_ms: float) -> int:
            return int(65535 * t_ms / 1000 * self.freq)

        def set_angle(self, degrees: float):
            super().set_angle(degrees)
            t_ms = self.t_0_ms + self.t_deg_ms * degrees
            duty = self.pwmduty_ms(t_ms)
            self.pwm.duty_cycle = duty

else:
    from board_io_windows import *
