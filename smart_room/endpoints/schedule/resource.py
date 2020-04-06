from datetime import datetime
import uuid

from flask import jsonify, make_response, current_app as app
from flask_restful import Resource, reqparse
from loguru import logger
from phue import Bridge

from utils.oauth import auth, g

from ..aircon.resource import control_aircon


BRIDGE_IP = "10.0.0.16"
bridge = Bridge(BRIDGE_IP)
bridge.connect()

def control_light(device, command):
    if device == "light_front":
        device_id = 1
    elif device == "light_back":
        device_id = 2
    logger.info(f"[Light Control]\nDevice: {device}\tAction: {command}")
    if command == 0 or command == "off":
        bridge.set_light(device_id, "on", False)
    elif command.isdigit():
        bridge.set_light(device_id, "on", True)
        bridge.set_light(device_id, "hue", 41442)
        bridge.set_light(device_id, "sat", 0)
        bridge.set_light(device_id, "bri", int(int(command) * 255 / 100))


class ScheduleResource(Resource):
    def __init__(self):
        # common parser
        self._set_common_parser()
        self._set_post_parser()
        self._set_put_parser()
        self._set_delete_parser()

    def _set_common_parser(self):
        self.common_parser = reqparse.RequestParser()
        self.common_parser.add_argument(
            "time",
            type=lambda x: datetime.strptime(x, "%Y-%m-%d %H:%M:%S"),
            required=True,
            location="json",
            help="Schedule: 'time' is required",
        )

    def _set_post_parser(self):
        def action_type(value):
            try:
                if not value["light_front"].isdigit() and not 0 <= int(value["light_front"]) <= 100:
                    raise ValueError("Incorrect light_front format, must between 0~100")
            except KeyError:
                raise ValueError("Missing light_front setting")
            try:
                if not value["light_back"].isdigit() and not 0 <= int(value["light_front"]) <= 100:
                    raise ValueError("Incorrect light_back format, must between 0~100")
            except KeyError:
                raise ValueError("Missing light_front setting")
            aircon_filter = (
                lambda x: x
                if str(x[:-1]).isdigit()
                and 16 <= int(x[:-1]) <= 30
                and x[-1] == "c"
                or x == "off"
                or x == "keep"
                else False
            )
            try:
                if not aircon_filter(value["aircon_front"]):
                    raise ValueError(
                        "Incorrect aircon_front format, must between 16c~30c or keep and off"
                    )
            except KeyError:
                raise ValueError("Missing aircon_front setting")
            try:
                if not aircon_filter(value["aircon_back"]):
                    raise ValueError(
                        "Incorrect aircon_back format, must between 16c~30c or keep and off"
                    )
            except KeyError:
                raise ValueError("Missing aircon_back setting")
            return value

        self.post_parser = self.common_parser.copy()
        self.post_parser.add_argument(
            "action",
            type=action_type,
            required=True,
            location="json",
            help="Schedule: 'action' is required",
        )

    def _set_put_parser(self):
        self.put_parser = self.common_parser.copy()
        self.put_parser.add_argument(
            "action",
            type=str,
            required=True,
            location="json",
            help="Schedule: 'action' is required",
        )
        self.put_parser.add_argument(
            "schedule_id",
            type=str,
            required=True,
            location="json",
            help="Put Schedule: 'schedule_id' is required",
        )

    def _set_delete_parser(self):
        self.delete_parser = reqparse.RequestParser()
        self.delete_parser.add_argument(
            "schedule_id",
            type=str,
            required=True,
            location="json",
            help="Delete Schedule: 'schedule_id' is required",
        )

    # pylint: disable=R0201
    @auth.login_required
    def get(self):
        logger.info(
            f"[Get Schedule Request]\nUser Account:{g.account}\nUUID:{g.uuid}\n"
        )
        # Return all schedules
        schedules = [
            {
                "schedule_id": schedule.id,
                "time": schedule.next_run_time.strftime("%Y-%m-%d %H:%M:%S"),
                "device": schedule.args[0],
                "command": schedule.args[1],
            }
            for schedule in app.apscheduler.get_jobs()
        ]
        return schedules

    # pylint: enable=R0201

    @auth.login_required
    def post(self):
        logger.info(
            f"[Post Schedule Request]\nUser Account:{g.account}\nUUID:{g.uuid}\n"
        )
        # Add new schedule
        args = self.post_parser.parse_args()

        job_types = {
            "light_front": control_light,
            "light_back": control_light,
            "aircon_front": control_aircon,
            "aircon_back": control_aircon,
        }
        jobs = {}
        for job_type in job_types:
            if args["action"][job_type] != "keep":
                jobs[job_type] = {
                    "action": args["action"][job_type],
                    "time": args["time"],
                    "user_id": g.uuid,
                    # database can handle uuid
                    "id": str(uuid.uuid4()),
                }
                # ---------------------------------
                # Future Work
                # Save job to database and get uuid
                # job = Schedule(**jobs[job_type])
                # Schedule.add(jobs[job_type])
                # ---------------------------------
                # Add to schedule
                schedule_result = app.apscheduler.add_job(
                    func=job_types[job_type],
                    trigger="date",
                    run_date=jobs[job_type]["time"],
                    args=[job_type, jobs[job_type]["action"]],
                    id=jobs[job_type]["id"],
                )
                logger.info(f"[Scheduler Add Job]\n{schedule_result}")
        return make_response(
            jsonify({"schedule_id": {job: jobs[job]["id"] for job in jobs}})
        )

    @auth.login_required
    def put(self):
        logger.info(
            f"[Put Schedule Request]\nUser Account:{g.account}\nUUID:{g.uuid}\n"
        )
        # Edit schedule
        args = self.put_parser.parse_args()
        app.apscheduler.modify_job(
            id=args["schedule_id"], next_run_time=args["time"], args=[args["action"]]
        )
        return make_response(jsonify({"status": "success"}))

    @auth.login_required
    def delete(self):
        logger.info(
            f"[Delete Schedule Request]\nUser Account:{g.account}\nUUID:{g.uuid}\n"
        )
        # Remove schedule
        args = self.delete_parser.parse_args()
        app.apscheduler.remove_job(args["schedule_id"])
        return make_response(jsonify({"status": "success"}))
