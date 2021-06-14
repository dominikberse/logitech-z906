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
        app.add_url_rule("/power", view_func=self._post_power, methods=['POST'])
        app.add_url_rule("/input", view_func=self._post_input, methods=['POST'])

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
            command = flask.request.json['command']
            self.command(self._commands[command])
            return flask.jsonify({})

        except:
            logging.exception('invalid request')
            return flask.jsonify({}), 400

    def _post_power(self):
        try:
            power = flask.request.json.get('power', True)
            if self._state.stage == Stage.Off and power:
                self.command(Commands.TurnOn)
            if self._state.stage == Stage.Ready and not power:
                self.command(Commands.TurnOff)
            return flask.jsonify({})

        except:
            logging.exception('invalid request')
            return flask.jsonify({}), 400

    def _post_input(self):
        try:
            input = flask.request.json['input']
            self.command(Commands.SelectInput, Input(input))
            return flask.jsonify({})

        except:
            logging.exception('invalid request')
            return flask.jsonify({}), 400
