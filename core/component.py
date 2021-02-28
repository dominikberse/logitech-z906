

class Component:
    """ Base class for components """

    def __init__(self, pi, state, queue):
        self._pi = pi
        self._state = state
        self._queue = queue
        self._asleep = False

    @property
    def asleep(self):
        return self._asleep

    @asleep.setter
    def asleep(self, asleep):
        self._asleep = asleep

    def command(self, command, *params, **kwargs):
        """ Shorthand to fire a command """
        self._queue.enqueue(command, *params, **kwargs)

    def update(self):
        """ Called upon state changes """
        pass


class PollingComponent(Component):

    def __init__(self, pi, state, queue):
        super().__init__(pi, state, queue)

    def poll(self):
        """ Called in main polling loop (if not asleep) """
        pass


class ConsumingComponent(Component):

    def __init__(self, pi, state, queue):
        super().__init__(pi, state, queue)

    def consume(self):
        """ Called upon enqueued commands """
        pass
