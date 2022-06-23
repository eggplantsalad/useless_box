from log import log


class ServoBase:
    # time_60_deg: time to move 60 degrees
    def __init__(self, time_60_deg: float):
        self.time_per_degree = time_60_deg / 60
        pass

    def set_angle(self, degrees: float):
        log('set servo: %.1f deg' % degrees, level=2)
