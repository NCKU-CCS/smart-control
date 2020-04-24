from flask import jsonify, make_response, current_app
from flask_restful import Resource, reqparse
from loguru import logger


from utils.oauth import auth, g
from .model import LightControl


class LightControlResource(Resource):
    def __init__(self):
        self._set_post_parser()
        self.bridge = current_app.config["BRIDGE"]

    def _set_post_parser(self):
        self.post_parser = reqparse.RequestParser()
        self.post_parser.add_argument(
            "action_front",
            type=int,
            choices=range(101),
            required=True,
            location="json",
            help="Post Light Control : 'action_front' need to set between 0 to 100",
        )
        self.post_parser.add_argument(
            "action_back",
            type=int,
            choices=range(101),
            required=True,
            location="json",
            help="Post Light Control : 'action_back' need to set between 0 to 100",
        )

    def control_light(self, command_front, command_back):
        logger.info(f"Light Control: {command_front}%, {command_back}%")
        action_set = []
        for index, command in enumerate((command_front, command_back)):
            device_id = index + 1
            if command == 0:
                self.bridge.set_light(device_id, "on", False)
                action_set.append(False)
            else:
                brightness = int(int(command) * 254 / 100)
                self.bridge.set_light(device_id, "on", True)
                self.bridge.set_light(device_id, "hue", 41442)
                self.bridge.set_light(device_id, "sat", 0)
                self.bridge.set_light(device_id, "bri", brightness)
                action_set.append(brightness)
        return action_set

    def get_light_status(self):
        light_status = []
        # there are two phue light
        for num in range(1, 3):
            # Get num light's on/off
            status = self.bridge.get_light(num, "on")
            # if light is on, get it's brightness
            if status:
                status = self.bridge.get_light(num, "bri")
            light_status.append(status)
        return light_status

    @auth.login_required
    def get(self):
        logger.info(f"[Get Aircon Request]\nUser Account:{g.account}\nUUID:{g.uuid}\n")
        light_status = self.get_light_status()
        response = {
            "status": {"light_front": light_status[0], "light_back": light_status[1]},
        }
        return jsonify(response)

    @auth.login_required
    def post(self):
        logger.info(f"[Post Aircon Request]\nUser Account:{g.account}\nUUID:{g.uuid}\n")
        args = self.post_parser.parse_args()
        # Execute
        action_set = self.control_light(args["action_front"], args["action_back"])
        # Save to database
        record = {
            "action_front": args["action_front"],
            "action_back": args["action_back"],
            "user_id": g.uuid,
        }
        LightControl(**record).add()
        # Get lights' status
        light_status = self.get_light_status()
        response = {
            "status": {"light_front": light_status[0], "light_back": light_status[1]},
        }
        # Check success or not
        if action_set == light_status:
            logger.success("Light Control Success")
            response["success"] = True
            return jsonify(response)
        logger.error("Light Control Faild")
        response["success"] = False
        return make_response(jsonify(response), 400)
