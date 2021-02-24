from core import PushingComponent
import pins

import pigpio
import board
import busio
import adafruit_ads1x15.ads1015 as ADS
from adafruit_ads1x15.analog_in import AnalogIn


class AnalogButton:
    """ Handles a single button """

    def __init__(self, range, func, limit=2):
        self.range = range
        self.func = func
        self.limit = limit

        self._level = 0

    def probe(self, voltage, state):
        """ Probe button and execute """

        # check if pressed
        toggled = self.range[0] < voltage < self.range[1]

        # flood bin (press)
        if toggled and self._level < self.limit:
            self._level += 1
            if self._level == self.limit:
                self.func(state)

        # drain bin (release)
        elif not toggled and self._level > 0:
            self._level -= 1


class Inputs(PushingComponent):
    """ Handles the inputs """

    AnalogButtons = [
        AnalogButton((0.180, 1.000), (lambda state: state.toggle_input())),
        AnalogButton((1.340, 1.360), (lambda state: state.toggle_mute())),
        AnalogButton((1.915, 1.935), (lambda state: state.toggle_speakers())),
        AnalogButton((2.515, 2.535), (lambda state: state.toggle_effect())),
    ]

    def __init__(self, pi, powered=False):
        self.pi = pi
        self.callbacks = {}
        self.levels = {}

        # analog inputs
        self.i2c = busio.I2C(board.SCL, board.SDA)
        self.ads = ADS.ADS1015(self.i2c)

        # power button
        self.powered = powered
        pi.set_glitch_filter(pins.ON_BUTTON, 10000)
        self.callbacks[pins.ON_BUTTON] = pi.callback(
            pins.ON_BUTTON,
            pigpio.RISING_EDGE,
            self._toggle_power)

        # analog (multiplexed) buttons
        self.buttons = AnalogIn(self.ads, ADS.P0)

        # rotary encoder
        self.last_rotary_gpio = None
        for button in (pins.POTI_1, pins.POTI_2):
            pi.set_glitch_filter(button, 10000)
            callback = pi.callback(button, pigpio.EITHER_EDGE, self._rotary)
            self.callbacks[button] = callback

    def _toggle_power(self, gpio, level, tick):
        """ Power button was pressed """

        # synchronize to main thread
        self.powered = not self.powered
        print('<power toggle>')

    def _rotary(self, gpio, level, tick):
        """ Rotary encoder ticked """

        self.levels[gpio] = level
        if all(self.levels.values()):
            if gpio == pins.POTI_1:
                self.state.increase_volume()
            if gpio == pins.POTI_2:
                self.state.decrease_volume()

    def push_state(self, state):
        """ Check for state updates and forward them """

        # turned off (check for power on only)
        if not state.powered and self.powered:
            state.powered = True
            state.booting = True

        # do not accept inputs until booted
        if not state.powered or state.booting:
            return

        # check for power down
        if not self.powered:
            state.powered = False
            return

        # read voltage and identify pressed buttons
        voltage = self.buttons.voltage
        for button in Inputs.AnalogButtons:
            button.probe(voltage, state)
