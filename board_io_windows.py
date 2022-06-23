# crappy workarounds for windows...
import pygame
import sys
import time

import board_io_base
import config


def await_switch(time_s: float) -> bool:
    ts_end = time.monotonic_ns() + (time_s * 1000 * 1000 * 1000)

    while True:
        ts_now = time.monotonic_ns()
        if ts_now > ts_end:
            return False

        event = pygame.event.poll()
        if event.type == pygame.NOEVENT:
            continue
        elif event.type == pygame.QUIT:
            sys.exit()
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_SPACE:
                return True
            elif event.key == pygame.K_ESCAPE or event.key == pygame.K_q:
                sys.exit()


def power_off():
    sys.exit(0)


class Servo(board_io_base.ServoBase):
    def __init__(self, time_60_deg: float, freq=100, t_0_ms=0.5, t_180_ms=2.5):
        super().__init__(time_60_deg)

    def set_angle(self, degrees: float):
        poll_pygame()

        super().set_angle(degrees)
        screen.fill('black')
        r = (degrees - config.angle_max) / (config.angle_off - config.angle_max)
        screen.fill('red', rect=(0, 90, int((1 - r) * 500), 20))
        pygame.display.flip()


# need to poll pygame every so often or it will hang
def poll_pygame():
    while True:
        event = pygame.event.poll()
        if event.type == pygame.NOEVENT:
            break


pygame.init()
pygame.display.set_caption('Useless box')
screen = pygame.display.set_mode((500, 200))
