from model import Input, Effect, Speakers
from core import PollingComponent
import pins

import pigpio
import copy


class Panel(PollingComponent):
    """ Controls the front panel """

    Leds = {
        pins.Q9: {
            pins.Q1: (lambda state: state.input == Input.Input1),
            pins.Q2: (lambda state: state.input == Input.Chinch),
            pins.Q3: (lambda state: state.input == Input.Optical),
            pins.Q5: (lambda state: state.input == Input.Input4),
            pins.Q6: (lambda state: state.input == Input.Input5),
            pins.Q7: (lambda state: state.input == Input.Aux),
            pins.Q8: (lambda state: state.decode),
            pins.Q10: (lambda state: False),
        },
        pins.Q11: {
            pins.Q1: (lambda state: state.speakers == Speakers.Front),
            pins.Q2: (lambda state: state.speakers == Speakers.Rear),
            pins.Q3: (lambda state: state.speakers == Speakers.Center),
            pins.Q5: (lambda state: state.speakers == Speakers.Front),
            pins.Q6: (lambda state: state.speakers == Speakers.Rear),
            pins.Q7: (lambda state: False),
            pins.Q8: (lambda state: state.speakers == Speakers.Sub),
            pins.Q10: (lambda state: False),
        },
        pins.Q12: {
            pins.Q1: (lambda state: state.volume / 4.0 - 10),
            pins.Q2: (lambda state: state.volume / 4.0 - 9),
            pins.Q3: (lambda state: state.volume / 4.0 - 8),
            pins.Q5: (lambda state: state.volume / 4.0 - 7),
            pins.Q6: (lambda state: state.volume / 4.0 - 6),
            pins.Q7: (lambda state: state.volume / 4.0 - 5),
            pins.Q8: (lambda state: state.volume / 4.0 - 4),
            pins.Q10: (lambda state: state.volume / 4.0 - 3),
        },
        pins.Q13: {
            pins.Q1: (lambda state: state.volume / 4.0 - 2),
            pins.Q2: (lambda state: state.volume / 4.0 - 1),
            pins.Q3: (lambda state: state.volume / 4.0),
            pins.Q5: (lambda state: state.effect == Effect._3D),
            pins.Q6: (lambda state: state.effect == Effect._4_1),
            pins.Q7: (lambda state: state.effect == Effect._2_1),
            pins.Q8: (lambda state: False),
            pins.Q10: (lambda state: False),
        },
    }

    Rows = [
        pins.Q9,
        pins.Q11,
        pins.Q12,
        pins.Q13,
    ]

    Cols = [
        pins.Q1,
        pins.Q2,
        pins.Q3,
        pins.Q5,
        pins.Q6,
        pins.Q7,
        pins.Q8,
        pins.Q10,
    ]

    def __init__(self, pi):
        self.pi = pi

        # references to the waves
        pi.wave_tx_stop()
        self._wave = None
        self._old = None

        # prepare power LED
        pi.set_mode(pins.Q4, pigpio.OUTPUT)

        # prepare all rows (-)
        self.all_rows_mask = 0
        for row in Panel.Rows:
            self.all_rows_mask |= 1 << row
            pi.set_mode(row, pigpio.OUTPUT)
            pi.write(row, 1)

        # prepare all cols (+)
        self.all_cols_mask = 0
        for col in Panel.Cols:
            self.all_cols_mask |= 1 << col
            pi.set_mode(col, pigpio.OUTPUT)
            pi.write(col, 0)

    def row_mask(self, row, state):
        """ Generate the LED bitmask (on) for the given row """

        mask = self.all_rows_mask & ~(1 << row)
        factor = None
        dim = 0

        for col, func in Panel.Leds[row].items():
            value = func(state)

            # non-dimmable LED
            if value is False:
                continue
            if value is True:
                mask |= 1 << col
                continue

            # dimmable LED
            if value >= 0.01:
                mask |= 1 << col

                if value <= 0.99:
                    dim = 1 << col
                    factor = value * value

        return (mask, dim, factor)

    def create_wave(self, state):
        """ Create wave for LED multiplexing """

        pulses = []
        for row in Panel.Rows:
            (turn_on, dim_off, factor) = self.row_mask(row, state)
            turn_off = ~turn_on & (self.all_rows_mask | self.all_cols_mask)

            if factor is None:
                # no dimmed LEDs
                pulses.append(pigpio.pulse(turn_on, turn_off, 1500))
            else:
                # single dimmed LED
                pulses.extend([
                    pigpio.pulse(turn_on, turn_off, int(1500 * factor)),
                    pigpio.pulse(0, dim_off, int(1500 * (1.0 - factor)))
                ])

        self.pi.wave_add_generic(pulses)
        return self.pi.wave_create()

    def poll_state(self, state):
        """ Update the panel to display given state """

        if self._old:
            # delete wave from last update cycle
            self.pi.wave_delete(self._old)
            self._old = None

        # show power state
        self.pi.write(pins.Q4, state.powered)

        # power down
        if not state.powered and self._wave:
            self.pi.wave_tx_stop()
            self._old = self._wave
            self._wave = None

        # update wave
        if state.powered and (state.trace or not self._wave):
            self._old = self._wave
            self._wave = self.create_wave(state)
            self.pi.wave_send_repeat(self._wave)
