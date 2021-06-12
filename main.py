
from core.model import State, Queue
from core.service import Service

from components.Z906.controller import Controller
from components.Z906.inputs import Inputs
from components.Z906.panel import Panel
from components.api import Api

import logging
import threading
import pigpio
import flask



if __name__ == "__main__":

    # initialize logging
    logging.basicConfig(level=logging.DEBUG)

    # initialize webserver
    app = flask.Flask("logitech-z906")

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
    service.register(Api(pi, state, queue, app))
    service.register(Controller(pi, state, queue))
    service.register(Inputs(pi, state, queue))
    service.register(Panel(pi, state, queue))

    # run application
    service.start()
    app.run(host='0.0.0.0')

    # shutdown
    pi.stop()
