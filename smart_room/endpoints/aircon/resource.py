import os

from flask import jsonify, make_response
from flask_restful import Resource, reqparse
from loguru import logger

from utils.oauth import auth, g
from .model import Aircon


def control_aircon(command_front, command_back):
    success = True
    for index, command in enumerate(command_front, command_back):
        cmd = f"irsend SEND_ONCE aircon {command}"
        returned = os.system(cmd)
        if returned != 0:
            success = False
            logger.error(f"[control_aircon] {index} set to {command} Fail!")
        else:
            logger.success(f"[control_aircon] {index} set to {command} Success!")
    return success


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
            help="Post Aircon : 'action_front' is required",
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
            help="Post Aircon : 'action_back' is required",
        )

    @auth.login_required
    def post(self):
        logger.info(
            f"[Post Aircon Request]\nUser Account:{g.account}\nUUID:{g.uuid}\n"
        )
        args = self.post_parser.parse_args()
        if args["action"]:
            # Execute
            returned_bool = control_aircon(args["action_front"], args["action_back"])
            # Save to database
            record = {
                "action_front": args["action_front"],
                "action_back": args["action_back"],
                "user_id": g.uuid,
            }
            Aircon(**record).add()
            if returned_bool is True:
                logger.success("A/C Control Success")
                return jsonify({"status": "success"})
            logger.error("A/C Control Faild")
        return make_response(jsonify({"status": "fail"}), 400)
