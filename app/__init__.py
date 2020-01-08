import os

from flask import Flask
from flask_restplus import Api
from .api.prng import bp, ns as prng_ns


def create_app(test_config=None):
    # create and configure the app
    app = Flask(__name__, instance_relative_config=True)
    api = Api(app=app, version='1.0', title='Remote Gaming Server API', description='RGS API', ui=True)

    ns = api.namespace('rng', description='PRNG operations')

    app.logger.info("Starting up")
    app.config.from_mapping(
        SECRET_KEY='dev',
        DATABASE=os.path.join(app.instance_path, 'app.sqlite'),
        LOG_LEVEL="ERROR",
        SWAGGER_URL="/swagger",
        API_URL="/static/swagger.json",
    )

    if test_config is None:
        # load the instance config, if it exists, when not testing
        app.config.from_pyfile('config.py', silent=True)
    else:
        # load the test config if passed in
        app.config.from_mapping(test_config)

    # ensure the instance folder exists
    try:
        os.makedirs(app.instance_path)
    except OSError:
        pass

    app.register_blueprint(bp)
    api.add_namespace(prng_ns)

    app.run(debug=True)

    return app
