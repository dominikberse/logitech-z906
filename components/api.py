from core.component import Component
from core.types import Commands, Stage, Input

import logging
import flask


class Api(Component):
    app = None

    def __init__(self, pi, state, queue, app):
        super().__init__(pi, state, queue)

        # register all known endpoints
        app.add_url_rule("/state", view_func=self._get_state, methods=['GET'])
        app.add_url_rule("/command", view_func=self._post_command, methods=['POST'])

        # register known commands
        self._commands = {
            'on': Commands.TurnOn,
            'off': Commands.TurnOff,
            'mute': Commands.Mute,
            'unmute': Commands.Unmute,
            'volume-up': Commands.VolumeUp,
            'volume-down': Commands.VolumeDown,
        }

    def _get_state(self):
        """ Get device state """

        return flask.jsonify({
            'power': self._state.stage == Stage.Ready,
        })

    def _post_command(self):
        """ Execute arbitrary command """
        try:

            # map and execute received command
            command = flask.request.json['command']
            self.command(self._commands[command], *params)
            return flask.jsonify({})

        except:
            logging.exception('invalid request')
            return flask.jsonify({}), 400



