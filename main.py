
from core.model import State, Queue
from core.service import Service
from components import api

from components.Z906.controller import Controller
from components.Z906.inputs import Inputs
from components.Z906.panel import Panel

import logging
import threading
import pigpio

if __name__ == "__main__":

    # initialize logging
    logging.basicConfig(level=logging.DEBUG)

    # load GPIO
    pi = pigpio.pi()
    if not pi.connected:
        logging.error("GPIO not available")
        exit(0)

    # initialize core
    state = State()
    queue = Queue()

    # initialize components
    service = Service(state, queue)
    service.register(api.Api(pi, state, queue))
    service.register(Controller(pi, state, queue))
    service.register(Inputs(pi, state, queue))
    service.register(Panel(pi, state, queue))

    # run application
    service.run()

    # shutdown
    pi.stop()
