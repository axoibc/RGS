#!/usr/bin/env python3





def validate_hash():
    """
    Validates hashes of all files every 24 hours. If the hashes are invalid, the system will be locked
    :return:
    """
    # Admin API
    admin_api = additionalAPIs.get("admin")

    # Check if the admin api exists
    if admin_api is not None:
        # Loop forever and verify the hashes every 24 hours
        while True:
            if admin_api.evaluate_system_hash() is False:
                with open(".lock", "w") as file:
                    file.write(str(admin_api.hash))

            # Sleep for 24 hours. 86400 is the number of seconds in 24 hours
            time.sleep(86400)
    else:
        logger.error("Error: There is no Admin API")


# Builds the standard classes needed for the game Models
system_config = Config("configs/server/SystemConfig.yaml")
database = None

# Initializing the logger
logging_level = system_config.get("loggingLevel", logger.ERROR)

logger.basicConfig(level=logging_level, format='%(asctime)s: [%(levelname)s] (%(threadName)-10s) %(message)s', )

# Sets the database to the correct type based on SystemConfig.json "storage" variable
if system_config.storage == "mongo":
    database = Database(system_config, Mongo(system_config.mongodb, logger))
elif system_config.storage == "memcache":
    database = Database(system_config, MemCache(system_config.memcache, logger))
else:
    logger.critical(
        "%s is not a valid storage value. Please change storage in SystemConfig.yaml" % system_config.storage)
    sys.exit("Invalid storage setting")

prng = Prng(system_config, logger)

connector = Connector("configs/connector/ConnectorConfig.yaml", database, logger)

# Initializes the Flask app
app = Flask(__name__)

additionalAPIs = dict()
# Adds addition API routes to app based on SystemConfig.json "additionalAPIs" variable
if system_config.additionalAPIs is not None:
    for api in system_config.additionalAPIs:
        api_module = Utilities.dynamic_import("API", system_config.additionalAPIs[api])
        additionalAPIs[api] = api_module.API(app, system_config, database, logger)

if system_config.dev is False:
    if system_config.get("disable_hash_verification", False) is False:
        # Creates a process to validate the hash of the system files
        validate_process = Process(target=validate_hash)
        validate_process.start()

# Creates a process to resolve any pending cycles
maintenance_process = Process(target=connector.start_maintenance)
maintenance_process.start()


# End point for the /idle API call
@app.route("/idle/<gameid>/<session>", methods=["GET"])
def get_idle(gameid, session):
    """
    Returns the availability of the game
    :param gameid: A unique ID for a game
    :param session: A unique ID for a session
    :return:
    """
    try:
        # Check for system lock
        if check_system_lock() is True:
            return log_and_return_error("Error: The system is locked")

        session = database.find_session_by_id(session)

        if session is None:
            return json.dumps({"error": "Error: Session is invalid"})

        return jsonpickle.encode(check_game_availability(gameid, session.get("variant"), session.get("site")),
                                 unpicklable=False)

    except Exception as error:
        return log_and_return_error(error)


# End point for the /initialize API call
@app.route("/initialize", methods=["POST"])
def post_initialize():
    """
    Calls the initialize function in the Model.py of a given game. Which Model.py to call is determined by the given
    gameid that is on the request object.
    :return: Response from Model.py initialize function
    """
    try:
        # Check for system lock
        if check_system_lock() is True:
            return log_and_return_error("Error: The system is locked")

        # Converts request object to json
        initialize = request.get_json()

        session = database.find_session_by_id(initialize.get("session"))
        gameid = session.get("game")
        basegame = session.get("basegame")
        if basegame is None:
            basegame = gameid

        if session is None:
            return json.dumps({"error": "Error: Session is invalid"})

        if check_game_availability(gameid, session.get("variant"), session.get("site")) is False:
            logger.info(
                "Game {} variant {} invalid or not enabled".format(gameid, session.get("variant")))
            return json.dumps({"error": "Error: Game/Variant/Site is not available"})

        # Gets the Model.py based on the given gameid
        module = Utilities.dynamic_import("Model", "games/" + basegame + "/Model.py")
        if module:
            model = module.Model(system_config, database, prng, connector, logger)
        else:
            raise FileNotFoundError("Model for game {} not found".format(basegame))

        # Calls model.initialize, turn the response into a json object, and returns that value to the front end
        return jsonpickle.encode(model.initialize(module.InitializeRequest(initialize)), unpicklable=False)

    except Exception as error:
        return log_and_return_error(error)


# End point for the /play API call
@app.route("/play", methods=["POST"])
def post_play():
    """
    Calls the play function in the Model.py of a given game. Which Model.py to call is determined by the given
    gameid that is on the request object.
    :return: Response from Model.py play function
    """
    try:
        # Check for system lock
        if check_system_lock() is True:
            return log_and_return_error("Error: The system is locked")

        # Converts request object to json
        play = request.get_json()

        session = database.find_session_by_id(play.get("session"))
        gameid = session.get("game")
        basegame = session.get("basegame")
        if basegame is None:
            basegame = gameid

        if session is None:
            return json.dumps({"error": "Error: Session is invalid"})

        if check_game_availability(gameid, session.get("variant"), session.get("site")) is False:
            return json.dumps({"error": "Error: Game is not available"})

        # Gets the Model.py based on the given gameid
        module = Utilities.dynamic_import("Model", "games/" + basegame + "/Model.py")
        if module:
            if system_config.dev is True:
                # if the games doesn't have an emulator install just use the Model.py file
                try:
                    emulator_module = Utilities.dynamic_import("Model", "games/" + basegame + "/Emulator.py")
                    model = emulator_module.Model(system_config, database, prng, connector, logger)
                except Exception:
                    model = module.Model(system_config, database, prng, connector, logger)
            else:
                model = module.Model(system_config, database, prng, connector, logger)
        else:
            raise FileNotFoundError("Model for game {} not found".format(basegame))

        # Calls model.play, turn the response into a json object, and returns that value to the front end
        return jsonpickle.encode(model.play(module.PlayRequest(play)), unpicklable=False)

    except Exception as error:
        return log_and_return_error(error)


# End point for the /recall API call
@app.route("/recall", methods=["POST"])
def post_recall():
    """
    Calls the recall function in the Model.py of a given game. Which Model.py to call is determined by the given
    gameid that is on the request object.
    :return: Response from Model.py recall function
    """
    try:
        # Check for system lock
        if check_system_lock() is True:
            return log_and_return_error("Error: The system is locked")

        # Converts request object to json
        recall = request.get_json()

        session = database.find_session_by_id(recall.get("session"))
        gameid = session.get("game")
        basegame = session.get("basegame")
        if basegame is None:
            basegame = gameid

        if session is None:
            return json.dumps({"error": "Error: Session is invalid"})

        if check_game_availability(gameid, session.get("variant"), session.get("site")) is False:
            return json.dumps({"error": "Error: Game is not available"})

        # Gets the Model.py based on the given gameid
        module = Utilities.dynamic_import("Model", "games/" + basegame + "/Model.py")
        model = module.Model(system_config, database, prng, connector, logger)

        # Calls model.recall, turn the response into a json object, and returns that value to the front end
        return jsonpickle.encode(model.recall(module.RecallRequest(recall)), unpicklable=False)

    except Exception as error:
        return log_and_return_error(error)


# End point for the /recovery API call
@app.route("/recovery", methods=["POST"])
def post_recovery():
    """
    Calls the recovery function in the Model.py of a given game. Which Model.py to call is determined by the given
    gameid that is on the request object.
    :return: Response from Model.py recovery function
    """
    try:
        # Check for system lock
        if check_system_lock() is True:
            return log_and_return_error("Error: The system is locked")

        # Converts request object to json
        recovery = request.get_json()

        session = database.find_session_by_id(recovery.get("session"))
        gameid = session.get("game")
        basegame = session.get("basegame")
        if basegame is None:
            basegame = gameid

        if session is None:
            return json.dumps({"error": "Error: Session is invalid"})

        if check_game_availability(gameid, session.get("variant"), session.get("site")) is False:
            return json.dumps({"error": "Error: Game is not available"})

        # Gets the Model.py based on the given gameid
        module = Utilities.dynamic_import("Model", "games/" + basegame + "/Model.py")
        model = module.Model(system_config, database, prng, connector, logger)

        # Calls model.recovery, turn the response into a json object, and returns that value to the front end
        return jsonpickle.encode(model.recovery(module.RecoveryRequest(recovery)), unpicklable=False)

    except Exception as error:
        return log_and_return_error(error)


# End point for the /rng API call
@app.route("/rng/<minimum>/<maximum>", methods=["GET"])
def get_rng(minimum, maximum):
    """
    Returns a list of random numbers between [minimum, maximum)
    :param minimum: The lowest number that can be returned (Inclusive)
    :param maximum: The largest number that can be returned (Exclusive)
    :return: [int]
    """
    try:
        # Check for system lock
        if check_system_lock() is True:
            return log_and_return_error("Error: The system is locked")

        count = request.args.get('count', 1)
        minimum = int(minimum)
        maximum = int(maximum)

        randnums = []

        # Appends count number of random ints to a list
        for i in range(int(count)):
            randnums.append(prng.random(minimum, maximum))

        # Returns list of random ints to the front end
        return json.dumps(randnums)

    except Exception as error:
        return log_and_return_error(error)


# End point for the /shuffle API call
@app.route("/shuffle/<unshuffled_list>", methods=["GET"])
def get_shuffle(unshuffled_list):
    """
    Randomly shuffles the order of the contents of a list
    :param unshuffled_list: Original list
    :return: []
    """
    try:
        # Check for system lock
        if check_system_lock() is True:
            return log_and_return_error("Error: The system is locked")

        # Returns the given list shuffled in a random order to the front end
        return json.dumps(prng.shuffle(json.loads(unshuffled_list)))

    except Exception as error:
        return log_and_return_error(error)


# End point for the /distribution API call
@app.route("/distribution", methods=["POST"])
def post_distribution():
    """
    Selects a random value from a weighted distribution. The distribution is a 2D array ([[x, y]...]) where x is the
    weight of the value y.
    :return: Random y value
    """
    try:
        # Check for system lock
        if check_system_lock() is True:
            return log_and_return_error("Error: The system is locked")

        # Returns a value from a weighted distribution to the front end
        return json.dumps(prng.distribution(request.get_json()))

    except Exception as error:
        return log_and_return_error(error)


def check_game_availability(gameid, variant, site=None):
    """
    Checks if the requested game is still enabled
    :param gameid: A unique ID for a game
    :param variant: A different RTP for a game
    :param site: Site parameter
    :return: boolean
    """
    # Forces game to always be enabled if SystemConfig.json "dev" variable is true
    if system_config.dev is True:
        return True

    # Find the game in the database
    game = Game().find(database, gameid, variant, site)

    return game.enabled


def log_and_return_error(error):
    """
    Logs error with a timestamp and then returns an error message to the front end
    :param error: Holds the information on what and where the caused the failure
    :return: json object
    """
    logger.exception(error, exc_info=True)
    return json.dumps({"error": "Service is unavailable at this time. Please try again."})


def check_system_lock():
    """
    Returns if the system is locked
    :return: Boolean
    """
    if system_config.get("disable_hash_verification"):
        return False

    return os.path.exists(".lock")
