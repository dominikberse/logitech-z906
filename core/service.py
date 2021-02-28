from .component import ConsumingComponent, PollingComponent
from .types import Stage

import logging
import threading
import time


class Worker:
    """ Works on a specific loop """

    def __init__(self, loop, description):
        self._loop = loop
        self._description = description
        self._thread = None
        self._cycle = 1

    @property
    def running(self):
        return self._thread is not None

    @property
    def cycle(self):
        return self._cycle

    def _guard(self):
        if self._thread is not None:
            logging.warning(f'already running: {self._description}')
            return False

        return True

    def _work(self):

        # start the thread (loop is long running)
        logging.info(f'running {self._description}')
        self._loop(self._cycle, self)

        # thread completed
        logging.info(f'stopped {self._description}')
        self._thread = None

    def run(self):
        """ Synchronously runs the worker """
        if not self._guard():
            return

        self._thread = threading.current_thread()
        self._work()

    def start(self):
        """ Asynchronously runs the worker """
        if not self._guard():
            return

        self._thread = threading.Thread(target=self._work)
        self._thread.start()
        return True

    def stop(self):
        """ Stop asynchronous worker """

        thread = self._thread
        if thread is None:
            logging.info(f'not running: {self._description}')
            return

        self._cycle += 1
        # thread.join()


class Service:
    """ Schedules the components """

    def __init__(self, state, queue):
        self._state = state
        self._queue = queue

        self._consumer = None
        self._components = []
        self._pollers = []
        self._running = True

        self._poll_worker = Worker(self._poll_loop, 'poll thread')
        self._queue_worker = Worker(self._queue_loop, 'queue thread')
        self._update_worker = Worker(self._update_loop, 'update thread')

    def _poll_loop(self, cycle, worker):
        """ Polling components loop """

        while cycle == worker.cycle:

            for component in self._pollers:
                component.poll()
            time.sleep(0.05)

    def _queue_loop(self, cycle, worker):
        """ Consuming component loop """

        if self._consumer is None:
            logging.error('missing consumer')
            return

        while self._running:

            self._queue.clear()
            self._consumer.consume()
            self._queue.wait()

    def _update_loop(self, cycle, worker):
        """ Main application loop """

        while self._running:

            self._state.clear()

            # start polling loop if neccessary
            if self._state.ready and not self._poll_worker.running:
                self._poll_worker.start()

            # run updates on components
            for component in self._components:
                component.update()

            # stop polling loop if neccessary
            if self._state.off and self._poll_worker.running:
                self._poll_worker.stop()

            self._state.wait()

    def register(self, component):
        if isinstance(component, ConsumingComponent):
            self._consumer = component
        if isinstance(component, PollingComponent):
            self._pollers.append(component)
        self._components.append(component)

    def run(self):
        self._queue_worker.start()
        self._update_worker.run()
