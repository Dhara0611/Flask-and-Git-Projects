from models.store import StoreModel
from models.item import ItemModel
from models.tag import TagModel
from models.item_tags import ItemTags
from models.user import UserModel

# by doing this, if we need to use models anywhere else can simply say- from models import StoreModel instead of 
# from models.store import StoreModel. 