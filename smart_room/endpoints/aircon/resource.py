import os
from datetime import datetime

from flask import jsonify, make_response
from flask_restful import Resource, reqparse
import pytz
from loguru import logger

from utils.oauth import auth, g

from .model import Aircon


def control_aircon(device, command):
    logger.info(f"[Aircon Control]\nDevice: {device}\tCommand: {command}")
    cmd = f"irsend SEND_ONCE aircon {command}"
    returned_value = os.system(cmd)
    return returned_value


class AirconResource(Resource):
    def __init__(self):
        self._set_post_parser()

    def _set_post_parser(self):
        self.post_parser = reqparse.RequestParser()
        self.post_parser.add_argument(
            "action_front",
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
        self.post_parser.add_argument(
            "action_back",
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
        logger.info(f"[Post Aircon Request]\nUser Account:{g.account}\nUUID:{g.uuid}\n")
        # Add new schedule
        args = self.post_parser.parse_args()
        if args["action_front"]:
            # Execute
            returned_value = control_aircon(1, args["action_front"])
            # Save to database
            record = {
                "action": args["action_front"],
                "time": datetime.now().astimezone(pytz.utc),
                "user_id": g.uuid,
            }
            Aircon.add(Aircon(**record))
            if returned_value == 0:
                return jsonify({"status": "success"})
        return make_response(jsonify({"status": "fail"}), 400)
