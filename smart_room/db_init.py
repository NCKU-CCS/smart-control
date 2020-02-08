# pylint: skip-file
import secrets

from werkzeug.security import generate_password_hash


############
#   User   #
############
user = {
    "account": "test",
    "password": generate_password_hash("test"),
    "tag": secrets.token_hex(),
}
