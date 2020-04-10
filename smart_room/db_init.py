# pylint: skip-file
import secrets

from werkzeug.security import generate_password_hash

from endpoints.user.model import User

############
#   User   #
############
user = {
    "account": "test",
    "password": generate_password_hash("test"),
    "token": secrets.token_hex(),
}
pi = {
    "account": "pi",
    "password": generate_password_hash("test"),
    "token": secrets.token_hex(),
}
User(**user).add()
User(**pi).add()
