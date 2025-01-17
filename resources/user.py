from flask.views import MethodView
from flask_smorest import Blueprint, abort
from passlib.hash import pbkdf2_sha256
from flask_jwt_extended import create_access_token,create_refresh_token,get_jwt_identity,jwt_required,get_jwt
from flask import jsonify

from db import db
from models import UserModel
from schemas import UserSchema
from sqlalchemy.exc import IntegrityError
from blocklist import BlOCKLIST

blp = Blueprint("Users", "users", description="Operations on users")

@blp.route("/register")
class UserRegister(MethodView):

    @blp.arguments(UserSchema)
    def post(self, user_data):
        
        user = UserModel(
            user = user_data["user"],
            password = pbkdf2_sha256.hash(user_data["password"])
        )
        try:
            db.session.add(user)
            db.session.commit()   
        except IntegrityError:
            abort(409, message="A user with that username already exists.")

        return {"message":"User created."}, 201

@blp.route("/login")
class UserLogin(MethodView):

    @blp.arguments(UserSchema)
    def post(self, user_data):
        user = UserModel.query.filter(
            UserModel.user == user_data["user"]
        ).first()

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

        
    
    

