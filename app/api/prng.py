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


@ns.route("/distribution/<distribution>", methods=["GET"])
class Distribution(Resource):

    @api.doc(responses={200: 'OK', 400: 'Bad Request', 500: 'General Error'},
             params={'distribution': 'The array to values and weights'},
             example={"[[1,10],[5,20],[3,30]]"}
             )
    def get(self, distribution):
        """
        Returns a random value from a weighted distribution
        :param distribution: 2D array ([[x, y]...]) where x is the value and y is the weight.
        :return: Random x value
        """
        try:
            dist_list = json.loads(distribution)

            if type(dist_list) is not list:
                raise TypeError("Distribution is not a list")

            # Find the total weight of the distribution
            distribution_max = 0

            for i in range(len(dist_list)):
                distribution_max += dist_list[i][1]

            # Generate a random number between [0, distribution_max)
            random_num = secrets.SystemRandom().randrange(0, distribution_max)
            distribution_value = 0

            # Find and return the weighted value from the distribution
            for i in range(len(dist_list)):
                distribution_value += dist_list[i][1]

                if random_num < distribution_value:
                    return dist_list[i][0]

        except Exception as error:
            abort(403, "Bad Request")
            current_app.logger.exception(error, exc_info=True)
