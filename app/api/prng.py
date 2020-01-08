from flask import (
    Blueprint, request, current_app
)

import json
import secrets
from werkzeug.exceptions import abort

from flask_restplus import Api, Resource, fields

bp = Blueprint('prng', __name__)

api = Api(bp, version='1.0', title='PRNG', description='PRNG API')

ns = api.namespace('rng', description='PRNG operations')


@ns.route("/<int:minimum>/<int:maximum>", methods=["GET"])
class Range(Resource):

    @api.doc(responses={200: 'OK', 400: 'Bad Request', 500: 'General Error'},
             params={'maximum': 'The range maximum', "minimum": "The range minimum",
                     "int:count": "Number of items to return"})
    def get(self, minimum, maximum):
        count = int(request.args.get('count', 1))
        minimum = int(minimum)
        maximum = int(maximum)
        randnums = []

        try:
            if minimum < 0:
                raise ValueError("Minimum value must be greater than 0")

            if maximum <= minimum:
                raise ValueError("Maximum value must be greater than minimum value")

            for i in range(int(count)):
                randnums.append(secrets.SystemRandom().randrange(minimum, maximum))

            return json.dumps(randnums)

        except ValueError as error:
            abort(403, "Bad Request")
            current_app.logger.critcial(error, exc_info=True)


@ns.route("/shuffle/<shuffled>", methods=["GET"])
class Shuffle(Resource):

    @api.doc(responses={200: 'OK', 400: 'Bad Request', 500: 'General Error'},
             params={'shuffled': 'The array to shuffle'})
    def get(self, shuffled):
        """
        Randomly shuffles the order of a list
        :param shuffled: Original list
        :example: http://127.0.0.1:5000/rng/shuffle/["AS","2S","3S","4S","5S","6S","7S","8C","9D","10H"]
        :return: []
        """
        try:
            shuffled_list = json.loads(shuffled)

            return json.dumps(secrets.SystemRandom().sample(shuffled_list, len(shuffled_list)))

        except Exception as error:
            abort(403, "Bad Request")
            current_app.logger.critcial(error, exc_info=True)
