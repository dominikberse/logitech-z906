from enum import IntEnum, Enum, Flag, auto


class Input(IntEnum):
    Unknown = 0
    Input1 = 1
    Chinch = 2
    Optical = 3
    Input4 = 4
    Input5 = 5
    Aux = 6


class Effect(IntEnum):
    Dolby = 0
    _3D = 1
    _4_1 = 2
    _2_1 = 3


class Speakers(IntEnum):
    NoSpeaker = 0
    Front = 1
    Rear = 2
    Center = 3
    Sub = 4


class State:
    """ Represents the global state """

    def __init__(self, max_volume):
        self.max_volume = max_volume
        self.booting = False
        self.powered = False
        self.trace = set()

        self._mute = False
        self._decode = False
        self._volume = 0
        self._input = None
        self._effect = None
        self._speakers = None

    @property
    def mute(self):
        return self._mute

    @mute.setter
    def mute(self, mute):
        self.trace.add('mute')
        self._mute = mute

    @property
    def volume(self):
        return self._volume

    @volume.setter
    def volume(self, volume):
        self.trace.add('volume')
        self._volume = volume

    @property
    def input(self):
        return self._input

    @input.setter
    def input(self, input):
        self.trace.add('input')
        self._input = input

    @property
    def effect(self):
        return self._effect

    @effect.setter
    def effect(self, effect):
        self.trace.add('effect')
        self._effect = effect

    @property
    def decode(self):
        return self._decode

    @decode.setter
    def decode(self, decode):
        self.trace.add('decode')
        self._decode = decode

    @property
    def speakers(self):
        return self._speakers

    @speakers.setter
    def speakers(self, speakers):
        self.trace.add('speakers')
        self._speakers = speakers

    def toggle_mute(self, mute):
        self.mute = not self._mute

    def increase_volume(self):
        if self._volume < self.max_volume:
            self.volume += 1

    def decrease_volume(self):
        if self._volume > 0:
            self.volume -= 1

    def toggle_input(self):
        if self._input is not None:
            self.input = Input(int(self._input) % 6 + 1)

    def toggle_effect(self, effect=None):
        if self._effect is not None:
            self.effect = Effect(int(self._effect) % 4 + 1)

    def toggle_speakers(self, speakers=None):
        if self._speakers is not None:
            self.speakers = Speakers((int(self._speakers) + 1) % 5)
