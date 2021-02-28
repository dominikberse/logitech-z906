from .types import Speakers, Input, Effect, Stage

import threading


class Queue:
    """ Stores commands sent to the device """

    def __init__(self):
        self._event = threading.Event()
        self._queue = []

    @property
    def drained(self):
        return not self._queue

    def enqueue(self, command, *params, **kwargs):
        self._queue.append((command, params, kwargs))
        self._event.set()

    def dequeue(self):
        if self._queue:
            return self._queue.pop(0)

    def clear(self):
        self._event.clear()

    def wait(self):
        self._event.wait()


class State:
    """ Stores the actual device state """

    def __init__(self, max_volume=43):
        self._max_volume = max_volume
        self._stage = Stage.Off
        self._mute = False
        self._decode = False
        self._input = Input.Input1
        self._speakers = Speakers.Master

        # volumes per speakers
        self._volumes = {
            Speakers.Master: 0,
            Speakers.Rear: max_volume / 2,
            Speakers.Center: max_volume / 2,
            Speakers.Sub: max_volume / 2,
        }

        # effects per input
        self._effects = {
            Input.Input1: Effect._2_1,
            Input.Chinch: Effect._2_1,
            Input.Aux: Effect._2_1,
        }

        # change notification
        self._event = threading.Event()

    @property
    def stage(self):
        return self._stage

    @property
    def mute(self):
        return self._mute

    @property
    def decode(self):
        return self._decode

    @property
    def input(self):
        return self._input

    @property
    def speakers(self):
        return self._speakers

    @property
    def effects(self):
        return self._effects

    @property
    def volumes(self):
        return self._volumes

    @property
    def volume(self):
        if self._speakers in self._volumes:
            return self._volumes[self._speakers]
        return 0

    @property
    def effect(self):
        if self._input in self._effects:
            return self._effects[self._input]
        return Effect.Dolby

    @property
    def ready(self):
        return self._stage >= Stage.Ready

    @property
    def powered(self):
        return self._stage >= Stage.Powered

    @property
    def off(self):
        return self._stage == Stage.Off

    def clear(self):
        self._event.clear()

    def wait(self):
        self._event.wait()
