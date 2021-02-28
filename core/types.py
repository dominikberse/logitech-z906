from enum import Enum, IntEnum, auto


class Input(IntEnum):
    Input1 = 0
    Chinch = 1
    Optical = 2
    Input4 = 3
    Input5 = 4
    Aux = 5

    @staticmethod
    def toggle(value):
        return (int(value) + 1) % 6


class Effect(IntEnum):
    _3D = 0
    _4_1 = 1
    _2_1 = 2
    Dolby = 3

    @staticmethod
    def toggle(value):
        return (int(value) + 1) % 4


class Speakers(IntEnum):
    Master = 0
    Front = 1
    Rear = 2
    Center = 3
    Sub = 4

    @staticmethod
    def toggle(value):
        return (int(value) + 1) % 5


class Stage(IntEnum):
    Off = 0
    Powered = 1
    Booting = 2
    Booted = 3
    Ready = 4


class Commands(Enum):
    TurnOn = auto()
    TurnOff = auto()
    Mute = auto()
    Unmute = auto()
    VolumeUp = auto()
    VolumeDown = auto()
    SelectInput = auto()
    SelectEffect = auto()
    RequestState = auto()
