from components import amp
from components import panel
from components import inputs
import model
import core

import pigpio
import time


if __name__ == "__main__":

    # load GPIO
    pi = pigpio.pi()
    if not pi.connected:
        print("GPIO not available")
        exit(0)

    # initialize model
    state = model.State(43)

    # load components
    components = [
        amp.Amplifier(pi),
        inputs.Inputs(pi),
        panel.Panel(pi),
    ]

    while True:

        # push updates to state
        for component in components:
            if isinstance(component, core.PushingComponent):
                component.push_state(state)

        # push updates to components
        for component in components:
            if isinstance(component, core.PollingComponent):
                component.poll_state(state)

        time.sleep(0.05)

    pi.stop()
