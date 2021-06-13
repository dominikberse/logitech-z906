from core.component import Component
from core.types import Commands, Stage, Input
from core.service import Worker

import evdev
import logging
import time


class LircCommand:
    """ Simple IR command """

    def __init__(self, callback, delay, repeatable=False):
        self._callback = callback
        self._delay = delay
        self._repeatable = repeatable
        self._latest = time.time()

    def execute(self):
        timestamp = time.time()

        # check if command can be executed
        if timestamp - self._latest < self._delay:
            if not self._repeatable:
                self._latest = timestamp
            return

        # execute command
        self._latest = timestamp
        self._callback()


class Lirc(Component, Worker):
    """ Handles the IR controller """

    def __init__(self, pi, state, queue):
        Component.__init__(self, pi, state, queue)
        Worker.__init__(self, self._loop, "IR thread")

        # known command list
        self._commands = {
            172160: LircCommand(self._toggle_power, 2.0),
            172040: LircCommand(self._toggle_input, 0.25),
            172266: LircCommand(self._toggle_mute, 0.25),
            172042: LircCommand(self._toggle_level, 0.25),
            172046: LircCommand(self._toggle_effect, 0.25),
            172202: LircCommand(self._volume_up, 0.1, repeatable=True),
            172138: LircCommand(self._volume_down, 0.1, repeatable=True),
        }

        # connect to LIRC
        self._lirc = evdev.InputDevice('/dev/input/event1')
        logging.info(self._lirc)

        # start event loop
        self.start()

    def _toggle_power(self):
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

    def _toggle_level(self):
        pass

    def _toggle_effect(self):
        pass

    def _volume_up(self):
        if self._state.stage == Stage.Ready:
            self.command(Commands.VolumeUp)

    def _volume_down(self):
        if self._state.stage == Stage.Ready:
            self.command(Commands.VolumeDown)

    def _loop(self, cycle, worker):
        """ Check for IR commands and forward them """

        while cycle == worker.cycle:
            event = self._lirc.read_one()
            if event is None:
                time.sleep(0.1)
                continue

            # map received command
            logging.info(f'received IR command: {event.value}')
            command = self._commands.get(event.value)

            # execute received command
            if command is not None:
                command.execute()