import os
from datetime import datetime
from flask import jsonify, make_response
from flask_restful import Resource, reqparse
import pytz

from utils.logging import logging
from utils.oauth import auth, g

from .model import Aircon


def control_aircon(command):
    cmd = f"irsend SEND_ONCE aircon {command}"
    returned_value = os.system(cmd)
    return returned_value


class AirconResource(Resource):
    def __init__(self):
        self._set_post_parser()

    def _set_post_parser(self):
        self.post_parser = reqparse.RequestParser()
        self.post_parser.add_argument(
            "action",
            type=lambda x: x
            if str(x[:-1]).isdigit()
            and 16 <= int(x[:-1]) <= 30
            and x[-1] == "c"
            or x == "off"
            else False,
            required=True,
            location="json",
            help="Post Aircon : 'action' is required",
        )

    @auth.login_required
    def post(self):
        logging.info(
            f"[Post Aircon Request]\nUser Account:{g.account}\nUUID:{g.uuid}\n"
        )
        args = self.post_parser.parse_args()
        if args["action"]:
            # Execute
            returned_value = control_aircon(args["action"])
            # Save to database
            record = {
                "action": args["action"],
                "time": datetime.now().astimezone(pytz.utc),
                "user_id": g.uuid,
            }
            Aircon.add(Aircon(**record))
            if returned_value == 0:
                return jsonify({"status": "success"})
        return make_response(jsonify({"status": "fail"}), 400)
