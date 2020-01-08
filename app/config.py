import os

SECRET_KEY = 'dev'
DATABASE = os.path.join(app.instance_path, 'app.sqlite')
LOG_LEVEL = "ERROR"
SWAGGER_URL = "/swagger"
API_URL = "/static/swagger.json"
