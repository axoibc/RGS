from flask import (Blueprint, flash, g, redirect, render_template, request, url_for)

import json
import secrets
from werkzeug.exceptions import abort

from app.logger import log

bp = Blueprint('prng', __name__)


@bp.route("/rng/<minimum>/<maximum>", methods=["GET"])
def get_range(minimum, maximum):
    count = request.args.get('count', 1)
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
        log().exception(error, exc_info=True)


@bp.route("/rng/shuffle/<shuffled>", methods=["GET"])
def shuffle(shuffled):
    """
    Randomly shuffles the order of a list
    :param shuffled: Original list
    :return: []
    """
    try:

        shuffled_list = json.loads(shuffled)

        return json.dumps(secrets.SystemRandom().sample(shuffled_list, len(shuffled_list)))

    except Exception as error:
        abort(402, "Bad Request")
        log().exception(error, exc_info=True)
