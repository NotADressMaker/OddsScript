from asgiref.wsgi import AsgiToWsgi
from mangum import Mangum

from api import app as fastapi_app

lambda_handler = Mangum(fastapi_app)
gcf_app = AsgiToWsgi(fastapi_app)
