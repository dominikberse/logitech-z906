from model import Input
from core import PollingComponent, PushingComponent
import pins

import pigpio
import serial
import time


class Commands:
    """ List of commands for the Logitech Z906 """

    Prefix = b'\xaa'
    SetState = b'\x0a'
    GetState = b'\x0a'

    On = b'\x11\x11\x15\x39\x38\x30\x39'
    Off = b'\x37'
    State = b'\x34'

    MasterUp = b'\x08'
    MasterDown = b'\x09'

    Inputs = {
        Input.Input1: b'\x02',
        Input.Chinch: b'\x05',
        Input.Optical: b'\x03',
        Input.Input4: b'\x04',
        Input.Input5: b'\x06',
        Input.Aux: b'\x07',
    }

    Mode = b'\x15'


class Amplifier(PollingComponent, PushingComponent):
    """ Provides communication with the main unit """

    def __init__(self, pi):
        self.pi = pi
        self.powered = False

        self.device = serial.Serial(
            '/dev/ttyAMA0',
            baudrate=57600,
            bytesize=serial.EIGHTBITS,
            parity=serial.PARITY_ODD,
            stopbits=serial.STOPBITS_ONE,
            xonxoff=False,
            rtscts=False,
            dsrdtr=False,
            timeout=0.5)

        # prepare power signal
        pi.set_mode(pins.ON_SIGNAL, pigpio.OUTPUT)
        pi.write(pins.ON_SIGNAL, 1)

    def _receive(self):
        """ Receive a well-formed message """

        header = self.device.read()
        if len(header) < 1:
            return False, None

        length = self.device.read()
        if len(length) < 1:
            return False, None

        body = self.device.read(length[0])
        if len(body) < length[0]:
            return False, None

        print('<< ' + str(body))
        return header, body

    def _check_mirror(self, message, start):
        """ Receive a mirrored message """

        if start[0] != message[0]:
            return False

        for expected in message[1:]:
            command = self.device.read()
            if len(command) < 1:
                return False
            if command[0] != expected:
                return False

        return True

    def _send(self, header, body):
        """ Send a well-formed message """

        # calculate missing bytes
        length = bytes(len(body))
        message = header + length + body
        checksum = self._checksum(message)

        # send combined message
        combined = Commands.Prefix + message + checksum
        self.device.write(combined)

        print('>>' + str(combined))

    def _checksum(self, data):
        """ Calculate a checksum over given bytes """

        checksum = 0
        for byte in data:
            checksum = (checksum + byte) % 255
        return checksum

    def _turn_on(self):
        """ Turn device on """

        # physical power on (short delay to ensure device is on)
        self.pi.write(pins.ON_SIGNAL, 0)
        time.sleep(2.0)

        # logical power on
        self.device.write(Commands.On)
        self.powered = True

    def _turn_off(self):
        """ Turn device off """

        # logical power off (delay to ensure state is stored)
        self.device.write(Commands.Off)
        time.sleep(5.0)

        # physical power off
        self.pi.write(pins.ON_SIGNAL, 1)
        self.powered = False

    def _request_state(self):
        """ Request current state """

        self.device.write(Commands.State)

    def _increase_volume(self):
        """ Increase volume level """

        self.device.write(Commands.MasterUp)

    def _decrease_volume(self):
        """ Increase volume level """

        self.device.write(Commands.MasterUp)

    def _select_input(self, input):
        """ Select given input """

        command = Commands.Inputs[input] + Commands.Mode
        self.device.write(command)

    def _set_state(self, state):
        """ Set completely new state """

        command = \
            bytes(state.volume) + \
            '\x15\x15\x15' + \
            bytes(state.input) + \
            '\x00\x00\x00' + \
            '\x01\x01\x01' + \
            '\x00\x00\x00' + \
            '\x06\x01\x03' + \
            '\x00\x00\x00'
        self._send(Commands.SetState, command)

    def _parse_message(self, header, body, state):
        """ Handle a well-formed message """

        if header[0] == Commands.GetState[0]:
            state.volume = body[0]
            state.input = body[4] + 1
            state.booting = False

    def _parse_next(self, command, state):
        """ Interpret the next byte """

        # handle full message
        if command[0] == Commands.Prefix[0]:
            header, body = self._receive()
            if header == False:
                return

            self._parse_message(header, body, state)

        elif self._check_mirror(Commands.On, command):
            self._request_state()
            print('<< power on')
        elif self._check_mirror(Commands.Off, command):
            print('<< power off')
        elif self._check_mirror(Commands.MasterUp, command):
            print('<< master up')
        elif self._check_mirror(Commands.MasterDown, command):
            print('<< master down')

    def poll_state(self, state):
        """ Update current state """
        pass

    def push_state(self, state):
        """ Trace current state """

        # power up
        if not self.powered and state.powered:
            self._turn_on()
            state.booting = True

        # power down
        if self.powered and not state.powered:
            state.powered = False
            self._turn_off()

        # read upcoming commands
        while self.device.in_waiting:
            command = self.device.read()
            if not command:
                return

            self._parse_next(command, state)
