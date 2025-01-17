from db import db
#green db - folder and blue is the Sqlalchemy object that is created inside it

class StoreModel(db.Model):
    __tablename__ = "stores"

    id = db.Column(db.Integer, primary_key = True)
    name = db.Column(db.String(80),unique=True, nullable=False)
    items=db.relationship("ItemModel", back_populates="store", lazy="dynamic")
    tags = db.relationship("TagModel", back_populates="store", lazy="dynamic")
    #cascade will delete the store even if items are not deleted.