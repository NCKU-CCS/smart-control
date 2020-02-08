# pylint: skip-file
import secrets

from werkzeug.security import generate_password_hash


############
#   User   #
############
user = {
    "account": "netdb",
    "password": generate_password_hash("netdb"),
    "tag": secrets.token_hex(),
}
