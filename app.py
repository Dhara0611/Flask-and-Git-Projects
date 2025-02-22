import os
import redis
from flask import Flask,jsonify
from flask_smorest import Api
from flask_jwt_extended import JWTManager
from flask_migrate import Migrate
from db import db
import models
from blocklist import BlOCKLIST
from dotenv import load_dotenv
from rq import Queue


from resources.item import blp as ItemBlueprint
from resources.store import blp as StoreBlueprint
from resources.tag import blp as TagBlueprint
from resources.user import blp as UserBlueprint


def create_app(db_url=None):
    app = Flask(__name__)
    load_dotenv()        #find .env and load its content.

    connection = redis.from_url(os.getenv("REDIS_URL"))
    app.queue = Queue("emails", connection=connection)

    app.config["PROPOGATE_EXCEPTIONS"]=True
    app.config["API_TITLE"]="Stores Rest API"
    app.config["API_VERSION"]="v1"
    app.config["OPENAPI_VERSION"]="3.0.3"
    app.config["OPENAPI_URL_PREFIX"]="/"
    app.config["OPENAPI_SWAGGER_UI_PATH"]="/swagger-ui"
    app.config["OPENAPI_SWAGGER_UI_URL"]="https://cdn.jsdelivr.net/npm/swagger-ui-dist/"
    app.config["SQLALCHEMY_DATABASE_URI"]= db_url or os.getenv("DATABASE_URL","sqlite:///data.db")
    #os.getenv - try to access the value of database variable, if it doesnot exists, it will use sqlite:///data.db
    db.init_app(app)
    migrate = Migrate(app, db)


    api = Api(app)

    app.config["JWT_SECRET_KEY"]="Dhara"
    jwt = JWTManager(app)


    @jwt.token_in_blocklist_loader
    def check_if_token_in_blocklist(jwt_header, jwt_payload):
        return jwt_payload["jti"] in BlOCKLIST

    @jwt.revoked_token_loader
    def revoked_token_callback(jwt_header, jwt_payload):
        return(
            jsonify(
                {
                    "description": "The token has been revoked.",
                    "error": "token_revoked"
                }
            ),401,
        )

    @jwt.needs_fresh_token_loader
    def token_not_fresh_callback(jwt_header, jwt_payload):
        return(
            jsonify(
                {
                    "description": "The token is not fresh.",
                    "error": "fresh_token_required."
                }
            ),401,
        )

    @jwt.expired_token_loader
    def expired_token_callback(jwt_header, jwt_payload):
        return (
            jsonify( 
                {"message":"The token has expired.",
                 "error":"token_expired"
                 }
                ),401,
        )

    @jwt.invalid_token_loader
    def invalid_token_callback(error):
        return(
            jsonify(
                {
                    "message": "Signature verification failed.",
                    "error" : "invalid_token",
                }
            ),401,
        )

    @jwt.unauthorized_loader
    def missing_token_callback(error):
        return(
                jsonify(
                    {
                        "description": "Request does not contain an access token",
                        "error" : "authorization_required",
                    }
                ),401,
            )
    #Since we will be using Flask-Migrate to create our database, we no longer need to tell Flask-SQLAlchemy to do it when we create the app.
    # with app.app_context():
    #     db.create_all()

    api.register_blueprint(ItemBlueprint)
    api.register_blueprint(StoreBlueprint)
    api.register_blueprint(TagBlueprint)
    api.register_blueprint(UserBlueprint)

    return app
