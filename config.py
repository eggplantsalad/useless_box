import sys

native = sys.platform == 'RP2040'

# logging level, higher is more logging
loglevel = 1

# for MG995 servo, we have 0.17s for 60 deg at 4.8V (and 0.13sec/60deg at 6V), both no-load
servo_time_60deg = 0.35

# if switch is not flipped in that time, power off
power_off_time_s = 20

# angles for servo: angle_off is default (power_off) position. angle_max turns the power off
angle_off = 120
angle_max = 17

if native:
    import board  # type: ignore
    # GPIO for switch, active-high
    gpio_switch = board.GP11

    # GPIO for power-outut / relay, active-high, we configure to pull-low to abort
    gpio_power_sel = board.GP12

    # GPIO for servo PWM
    gpio_servo = board.GP13

    # CP has no typing module
    have_typing = False
else:
    # Assuming typing module presence
    have_typing = True
