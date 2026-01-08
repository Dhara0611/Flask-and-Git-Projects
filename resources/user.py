import os
import requests
from flask.views import MethodView
from flask_smorest import Blueprint, abort
from passlib.hash import pbkdf2_sha256
from flask_jwt_extended import create_access_token,create_refresh_token,get_jwt_identity,jwt_required,get_jwt
from flask import jsonify 
from sqlalchemy import or_
from flask import current_app


from db import db
from models import UserModel
from schemas import UserSchema,UserRegisterSchema
from sqlalchemy.exc import IntegrityError
from blocklist import BlOCKLIST
from tasks import send_user_registration_email

blp = Blueprint("Users", "users", description="Operations on users")

def send_simple_message(to,subject,body):
    domain=os.getenv("MAILGUN_DOMAIN")
    response = requests.post(
        f"https://api.mailgun.net/v3/{domain}/messages",
  		auth=("api", os.getenv("MAILGUN_API_KEY")),
  		data={"from": f"Dhara Deshpande <mailgun@{domain}>",
  			"to": [to],
  			"subject": subject,
  			"text": body})
    return response


@blp.route("/register")
class UserRegister(MethodView):

    @blp.arguments(UserRegisterSchema)
    def post(self, user_data):
        if UserModel.query.filter(
            or_(
                UserModel.email == user_data["email"],
                UserModel.username == user_data["username"]
            ) #or_ checks that either email or username is true
            ).first():
            abort(409, message="A user with that username or email already exists!")
        
        user = UserModel(
            username = user_data["username"],
            email=user_data["email"],
            password = pbkdf2_sha256.hash(user_data["password"])
        )
        db.session.add(user)
        db.session.commit()   

        #enqueue function schedules the send_user_registration_email function to be executed later by a worker (a background process).
        current_app.queue.enqueue(send_user_registration_email,user.email,user.username)
        #The Redis queue (emails) will hold this job until a worker picks it up.
        
        return {"message":"User created."}, 201



@blp.route("/login")
class UserLogin(MethodView):

    @blp.arguments(UserSchema)
    def post(self, user_data):
        user = UserModel.query.filter(
            UserModel.username == user_data["username"]
        ).first()
        #if user exists, we hash the password and verify it with the one that is hashed and saved in User database. \
        #we do not unhash the passwords.
        if user and pbkdf2_sha256.verify(user_data["password"],user.password):
            access_token = create_access_token(identity=str(user.id), fresh=True)
            refresh_token = create_refresh_token(identity=str(user.id))

            return {"access_token": access_token, "refresh_token" : refresh_token}
        
        abort(401, message="Invalid credentials.")

@blp.route("/refresh")
class TokenRefresh(MethodView):

    @jwt_required(refresh=True)
    def post(self):
        current_user = get_jwt_identity()
        new_token = create_access_token(identity=str(current_user), fresh=False)
        #if you want refresh token to expire, you can add jti to blocklist. 
        jti = get_jwt()["jti"]
        BlOCKLIST.add(jti)
        
        return {"access_token": new_token}

@blp.route("/logout")
class UserLogout(MethodView):
    @jwt_required()
    def post(self):
        jti = get_jwt()["jti"]
        BlOCKLIST.add(jti)
        return {"message": "Successfully logged out"}, 200


@blp.route("/user/<int:user_id>")
class User(MethodView):

    @blp.response(200, UserSchema)
    def get(self, user_id):
        user = UserModel.query.get_or_404(user_id)
        return user
    

    def delete(self, user_id):
        user = UserModel.query.get_or_404(user_id)
        db.session.delete(user)
        db.session.commit()
        return{"message":"User deleted."},200

        
    
    

