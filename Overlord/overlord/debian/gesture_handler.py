import logging
import time

from PyQt6.QtCore import QObject, pyqtSignal

from ..config import (
    CORNER_SIZE,
    DOUBLE_TAP_INTERVAL,
    TAP_INTERVAL,
    SEQUENCE_TIMEOUT,
    GESTURE_CORNER_DOUBLE_TAP,
    GESTURE_FIVE_TAP_ANYWHERE,
    GESTURE_CORNER_SEQUENCE,
)

logger = logging.getLogger("overlord")


class GestureHandler(QObject):

    gesture_triggered = pyqtSignal()

    CORNER_TL = 0
    CORNER_TR = 1
    CORNER_BR = 2
    CORNER_BL = 3

    def __init__(self, gesture_type: str, parent=None):
        super().__init__(parent)
        self._gesture_type = gesture_type
        self._last_tap_time = 0
        self._last_tap_corner = -1
        self._tap_count = 0
        self._sequence_tap_corner = -1
        self._sequence_stage = 0
        self._sequence_start_time = 0

    def set_gesture_type(self, gesture_type: str):
        self._gesture_type = gesture_type
        self._reset_state()

    def handle_corner_click(self, x: int, y: int, screen_width: int, screen_height: int):
        corner = self._detect_corner(x, y, screen_width, screen_height)
        if corner is None:
            return
        current_time = time.time() * 1000
        logger.debug("Corner clicked: %d, gesture: %s", corner, self._gesture_type)

        if self._gesture_type == GESTURE_CORNER_DOUBLE_TAP:
            self._process_double_tap(corner, current_time)
        elif self._gesture_type == GESTURE_FIVE_TAP_ANYWHERE:
            self._process_five_tap(corner, current_time)
        elif self._gesture_type == GESTURE_CORNER_SEQUENCE:
            self._process_corner_sequence(corner, current_time)

    def handle_any_tap(self, x: int, y: int, screen_width: int, screen_height: int):
        if self._gesture_type == GESTURE_FIVE_TAP_ANYWHERE:
            current_time = time.time() * 1000
            self._process_five_tap(-1, current_time)

    def _detect_corner(self, x: int, y: int, w: int, h: int) -> int | None:
        in_top = y <= CORNER_SIZE
        in_bottom = y >= h - CORNER_SIZE
        in_left = x <= CORNER_SIZE
        in_right = x >= w - CORNER_SIZE

        if in_top and in_left:
            return self.CORNER_TL
        elif in_top and in_right:
            return self.CORNER_TR
        elif in_bottom and in_right:
            return self.CORNER_BR
        elif in_bottom and in_left:
            return self.CORNER_BL
        return None

    def _process_double_tap(self, corner: int, current_time: float):
        if (self._last_tap_corner == corner
                and current_time - self._last_tap_time < DOUBLE_TAP_INTERVAL
                and self._last_tap_time > 0):
            logger.debug(">>> DOUBLE TAP DETECTED <<<")
            self.gesture_triggered.emit()
            self._reset_state()
        else:
            self._last_tap_time = current_time
            self._last_tap_corner = corner

    def _process_five_tap(self, corner: int, current_time: float):
        if current_time - self._last_tap_time < TAP_INTERVAL and self._last_tap_time > 0:
            self._tap_count += 1
            logger.debug("Tap %d/5", self._tap_count)
            if self._tap_count >= 5:
                logger.debug(">>> 5 TAPS DETECTED <<<")
                self.gesture_triggered.emit()
                self._reset_state()
        else:
            self._tap_count = 1
        self._last_tap_time = current_time

    def _process_corner_sequence(self, corner: int, current_time: float):
        if self._sequence_start_time > 0 and current_time - self._sequence_start_time > SEQUENCE_TIMEOUT:
            self._reset_state()

        if self._sequence_start_time == 0:
            self._sequence_start_time = current_time

        if corner == self.CORNER_TL:
            if self._sequence_stage == 0:
                self._sequence_stage = 1
                self._sequence_tap_corner = corner
            elif self._sequence_stage == 1 and self._sequence_tap_corner == self.CORNER_TL:
                self._sequence_stage = 2
        elif corner == self.CORNER_BR:
            if self._sequence_stage == 2:
                self._sequence_tap_corner = corner
                self._sequence_stage = 3
            elif self._sequence_stage == 3 and self._sequence_tap_corner == self.CORNER_BR:
                logger.debug(">>> CORNER SEQUENCE DETECTED <<<")
                self.gesture_triggered.emit()
                self._reset_state()
                return

        self._last_tap_time = current_time

    def _reset_state(self):
        self._last_tap_time = 0
        self._last_tap_corner = -1
        self._tap_count = 0
        self._sequence_tap_corner = -1
        self._sequence_stage = 0
        self._sequence_start_time = 0
