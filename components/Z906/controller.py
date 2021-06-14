from core.component import ConsumingComponent
from core.types import Input, Speakers, Effect, Stage, Commands
from core.service import Worker
from core import pins

import logging
import serial
import pigpio
import time


class Mappings:

    Inputs = {
        Input.Input1: b'\x02',
        Input.Chinch: b'\x05',
        Input.Optical: b'\x03',
        Input.Input4: b'\x04',
        Input.Input5: b'\x06',
        Input.Aux: b'\x07',
    }

    Effects = {
        Effect.Dolby: b'\x35',
        Effect._3D: b'\x14',
        Effect._4_1: b'\x15',
        Effect._2_1: b'\x16',
    }

    VolumeUp = {
        Speakers.Master: b'\x08',
        Speakers.Center: b'\x0c',
        Speakers.Rear: b'\x0e',
        Speakers.Sub: b'\x0a',
    }

    VolumeDown = {
        Speakers.Master: b'\x09',
        Speakers.Center: b'\x0d',
        Speakers.Rear: b'\x0f',
        Speakers.Sub: b'\x0b',
    }


class Reader(Worker):
    """ Receives incoming data """

    def __init__(self, delegate, serial):
        super().__init__(self._read, 'serial thread')

        self._delegate = delegate
        self._serial = serial

    def _log(self, *params):
        """ Logs the given message """

        data = b'|'.join(params)
        logging.debug(f'<< {data}')

    def _read(self, cycle, worker):
        """ Receives incoming serial commands """

        while cycle == worker.cycle:

            data = self._serial.read()
            if not data:
                continue

            elif data == b'\xaa':
                self._message()
            elif data == b'\x11':
                self._on()
            elif data == b'\x37':
                self._off()
            elif data in Mappings.VolumeUp.values():
                self._volume_up(data)
            elif data in Mappings.VolumeDown.values():
                self._volume_down(data)
            elif data in Mappings.Inputs.values():
                self._input_selected(data)
            elif data == b'\x18':
                pass
            else:
                logging.warning(f'unknown byte {data}')

    def _message(self):
        """ Read a well-formed message """

        marker = self._serial.read()
        if not marker:
            return

        length = self._serial.read()
        if not length:
            return

        length = int(length[0])
        content = self._serial.read(length)
        if len(content) < length:
            return

        # message parsed successfully
        if marker == b'\x0a':
            self._state(content)
        else:
            logging.warning(f'unknown marker: {marker}')

    def _on(self):
        data = self._serial.read(6)

        self._log(b'on', data)
        self._delegate._notify_on()

    def _off(self):

        self._log(b'off')
        self._delegate._notify_off()

    def _volume_up(self, data):

        self._log(b'volume up', data)
        for speakers, command in Mappings.VolumeUp.items():
            if command == data:
                self._delegate._notify_volume_up(speakers)
                return

    def _volume_down(self, data):

        self._log(b'volume down', data)
        for speakers, command in Mappings.VolumeDown.items():
            if command == data:
                self._delegate._notify_volume_down(speakers)
                return

    def _input_selected(self, data):

        self._log(b'input selected', data)
        for input, command in Mappings.Inputs.items():
            if command == data:
                self._delegate._notify_input_selected(input)
                return

    def _state(self, content):

        self._log(b'state', content)
        self._delegate._notify_state(
            volumes={
                Speakers.Master: int(content[0]),
                Speakers.Rear: int(content[1]),
                Speakers.Center: int(content[2]),
                Speakers.Sub: int(content[3]),
            },
            input=Input(content[4]),
            effects={
                Input.Chinch: int(content[8]),
                Input.Aux: int(content[9]),
                Input.Input1: int(content[10]),
            })


class Writer:
    """ Transmits outgoing data """

    def __init__(self, serial):
        self._serial = serial

    @staticmethod
    def checksum(data):
        """ Calculate a checksum over given bytes """

        checksum = 0
        for byte in data:
            checksum = (checksum + byte) % 255
        return checksum

    @staticmethod
    def message(marker, content):
        """ Format a well-formed message """

        # calculate missing bytes
        length = bytes(len(content))
        message = marker + length + content
        checksum = Commands.checksum(message)

        # build complete message
        return b'\xaa' + message + checksum

    @staticmethod
    def on(effect=Effect.Dolby):
        return b'\x11\x11' + Mappings.Effects[effect] + b'\x39\x38\x30\x39'

    @staticmethod
    def off():
        return b'\x37'

    @staticmethod
    def request_state():
        return b'\x34'

    @staticmethod
    def volume_up(speakers=Speakers.Master):
        return Mappings.VolumeUp[speakers]

    @staticmethod
    def volume_down(speakers=Speakers.Master):
        return Mappings.VolumeDown[speakers]

    @staticmethod
    def select_input(input, effect=Effect.Dolby):
        return Mappings.Inputs[input] + Mappings.Effects[effect]

    @staticmethod
    def select_effect(effect, input):
        pass

    @staticmethod
    def set_state(volumes, input, effects):
        content = \
            bytes(volumes[Speakers.Master]) + \
            bytes(volumes[Speakers.Rear]) + \
            bytes(volumes[Speakers.Center]) + \
            bytes(volumes[Speakers.Sub]) + \
            bytes(input) + \
            b'\x00\x00\x00' + \
            bytes(effects[Input.Chinch]) + \
            bytes(effects[Input.Aux]) + \
            bytes(effects[Input.Input1]) + \
            b'\x00\x00\x00' + \
            b'\x06\x01\x03' + \
            b'\x00\x00\x00'
        return Commands.message(b'\x0a', content)

    def write(self, command, **kwargs):
        """ Transfer command (an log) """

        # build command and log it
        data = command(**kwargs)
        logging.debug(f">> {data}")

        # send command to device
        self._serial.write(data)


class Controller(ConsumingComponent):
    """ Provides serial communication with the Z906 main unit """

    def __init__(self, pi, state, queue):
        super().__init__(pi, state, queue)

        # connect to main unit
        self._serial = serial.Serial(
            '/dev/ttyAMA0',
            baudrate=57600,
            bytesize=serial.EIGHTBITS,
            parity=serial.PARITY_ODD,
            stopbits=serial.STOPBITS_ONE,
            xonxoff=False,
            rtscts=False,
            dsrdtr=False,
            timeout=1.0)

        # must stay at ground
        self._pi.write(pins.ON_SIGNAL, 0)

        # initialize communication helpers
        self._reader = Reader(self, self._serial)
        self._writer = Writer(self._serial)

        # build list of supported commands
        self._handlers = {
            Commands.TurnOn: self._turn_on,
            Commands.TurnOff: self._turn_off,
            Commands.Mute: self._mute,
            Commands.Unmute: self._unmute,
            Commands.VolumeUp: self._volume_up,
            Commands.VolumeDown: self._volume_down,
            Commands.SelectInput: self._select_input,
            Commands.SelectEffect: self._select_effect,
            Commands.RequestState: self._request_state,
        }

    def _execute(self, command, *params, **kwargs):
        if command in self._handlers:
            self._handlers[command](*params, **kwargs)

    def _turn_on(self):
        self._reader.start()
        self._state._stage = Stage.Booting
        self._writer.write(Writer.on)

    def _turn_off(self):
        self._writer.write(Writer.off)

    def _mute(self):
        pass

    def _unmute(self):
        pass

    def _volume_up(self, speakers=None):
        if speakers is None:
            speakers = self._state.speakers
        self._writer.write(Writer.volume_up, speakers=speakers)

    def _volume_down(self, speakers=None):
        if speakers is None:
            speakers = self._state.speakers
        self._writer.write(Writer.volume_down, speakers=speakers)

    def _select_input(self, input):
        self._writer.write(Writer.select_input, input=input)

    def _select_effect(self, effect, input=None):
        if input is None:
            input = self._state.input
        self._writer.write(Writer.select_effect, effect=effect, input=input)

    def _request_state(self):
        pass

    def _notify_on(self):
        self._state._stage = Stage.Booted
        self._state._event.set()

        # request initial state
        self._writer.write(Writer.request_state)

    def _notify_off(self):
        self._reader.stop()
        self._state._stage = Stage.Off
        self._state._event.set()

    def _notify_volume_up(self, speakers):
        self._state._volumes[speakers] += 1
        self._state._event.set()

    def _notify_volume_down(self, speakers):
        self._state._volumes[speakers] -= 1
        self._state._event.set()

    def _notify_input_selected(self, input):
        self._state._input = input
        self._state._event.set()

    def _notify_state(self, volumes, input, effects):
        self._state._stage = Stage.Ready
        self._state._volumes = volumes
        self._state._input = input
        self._state._effects = effects
        self._state._event.set()

    def consume(self):
        """ Execute all commands from queue """

        while not self._queue.drained:
            (command, params, kwargs) = self._queue.dequeue()
            self._execute(command, *params, **kwargs)
