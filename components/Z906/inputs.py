from core.component import PollingComponent
from core.types import Commands, Stage, Input
from core import pins

import logging
import pigpio
import board
import busio

import RPi.GPIO as gpio
import adafruit_ads1x15.ads1015 as ADS
from adafruit_ads1x15.analog_in import AnalogIn


class AnalogButton:
    """ Handles a single button """

    def __init__(self, levels, command, limit=2):
        self._levels = levels
        self._command = command
        self._limit = limit
        self._counter = 0

    def probe(self, voltage, parent):
        """ Probe button and execute """

        # check if pressed
        toggled = self._levels[0] < voltage < self._levels[1]

        # flood bin (press)
        if toggled and self._counter < self._limit:
            self._counter += 1
            if self._counter == self._limit:
                self._command(parent)

        # drain bin (release)
        elif not toggled and self._counter > 0:
            self._counter -= 1


class Inputs(PollingComponent):
    """ Handles the inputs """

    AnalogButtons = [
        AnalogButton((0.150, 0.170), (lambda self: self._toggle_input())),
        AnalogButton((1.320, 1.380), (lambda self: self._toggle_mute())),
        AnalogButton((1.895, 1.955), (lambda self: self._toggle_speakers())),
        AnalogButton((2.495, 2.555), (lambda self: self._toggle_effect())),
    ]

    def __init__(self, pi, state, queue):
        super().__init__(pi, state, queue)
        self.callbacks = {}
        self.levels = {}

        # analog inputs
        self.i2c = busio.I2C(board.SCL, board.SDA)
        self.ads = ADS.ADS1015(self.i2c)

        # power button
        gpio.setmode(gpio.BCM)
        gpio.setup(pins.ON_BUTTON, gpio.IN)
        gpio.add_event_detect(
            pins.ON_BUTTON, gpio.RISING,
            callback=self._toggle_power,
            bouncetime=200)

        # analog (multiplexed) buttons
        self.buttons = AnalogIn(self.ads, ADS.P0)

        # rotary encoder
        self.last_rotary_gpio = None
        for button in (pins.POTI_1, pins.POTI_2):
            gpio.setup(button, gpio.IN)
            gpio.add_event_detect(
                button, gpio.BOTH,
                callback=self._rotary,
                bouncetime=20)

    def _toggle_power(self, channel):
        logging.info('pressed: power button')
        if self._state.stage == Stage.Ready:
            self.command(Commands.TurnOff)
        elif self._state.stage == Stage.Off:
            self.command(Commands.TurnOn)

    def _toggle_input(self):
        input = Input.toggle(self._state.input)
        self.command(Commands.SelectInput, input)

    def _toggle_mute(self):
        if self._state.mute:
            self.command(Commands.Unmute)
        else:
            self.command(Commands.Mute)

    def _toggle_speakers(self):
        pass

    def _toggle_effect(self):
        pass

    def _rotary(self, channel):
        """ Rotary encoder ticked """

        self.levels[channel] = gpio.input(channel)
        if all(self.levels.values()):
            if channel == pins.POTI_1:
                self.command(Commands.VolumeUp)
            if channel == pins.POTI_2:
                self.command(Commands.VolumeDown)

    def poll(self):
        """ Check for state updates and forward them """

        # read voltage and identify pressed buttons
        voltage = self.buttons.voltage
        for button in Inputs.AnalogButtons:
            button.probe(voltage, self)

        if voltage < 3.0:
            logging.debug(f'input: {voltage}')
