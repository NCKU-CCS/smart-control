import os
from datetime import datetime
from flask import jsonify, make_response, current_app as app
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
        # Add new schedule
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


class AirconScheduleResource(Resource):
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
            help="Put Aircon Schedule: 'time' is required",
        )
        self.common_parser.add_argument(
            "action",
            type=lambda x: x
            if str(x[:-1]).isdigit()
            and 16 <= int(x[:-1]) <= 30
            and x[-1] == "c"
            or x == "off"
            else False,
            required=True,
            location="json",
            help="Put Aircon Schedule: 'action' is required",
        )

    def _set_post_parser(self):
        self.post_parser = self.common_parser.copy()

    def _set_put_parser(self):
        self.put_parser = self.common_parser.copy()
        self.put_parser.add_argument(
            "schedule_id",
            type=str,
            required=True,
            location="json",
            help="Put Aircon Schedule: 'schedule_id' is required",
        )

    def _set_delete_parser(self):
        self.delete_parser = reqparse.RequestParser()
        self.delete_parser.add_argument(
            "schedule_id",
            type=str,
            required=True,
            location="json",
            help="Delete Aircon Schedule: 'schedule_id' is required",
        )

    # pylint: disable=R0201
    @auth.login_required
    def get(self):
        logging.info(
            f"[Get Aircon Schedule Request]\nUser Account:{g.account}\nUUID:{g.uuid}\n"
        )
        # Return all schedules
        schedules = [
            {
                "schedule_id": schedule.id,
                "time": schedule.next_run_time.strftime("%Y-%m-%d %H:%M:%S"),
                "action": schedule.args[0],
            }
            for schedule in app.apscheduler.get_jobs()
        ]
        return schedules

    # pylint: enable=R0201

    @auth.login_required
    def post(self):
        logging.info(
            f"[Post Aircon Schedule Request]\nUser Account:{g.account}\nUUID:{g.uuid}\n"
        )
        # Add new schedule
        args = self.post_parser.parse_args()
        # Save job to database and get uuid
        job_result = {
            "action": args["action"],
            "time": args["time"],
            "user_id": g.uuid,
        }
        job = Aircon(**job_result)
        Aircon.add(job)
        # Add to schedule
        schedule_result = app.apscheduler.add_job(
            func=control_aircon,
            trigger="date",
            run_date=job_result["time"],
            args=[job_result["action"]],
            id=job.uuid,
        )
        logging.info(f"[Scheduler Add Job]\n{schedule_result}")
        return make_response(jsonify({"schedule_id": job.uuid}))

    @auth.login_required
    def put(self):
        logging.info(
            f"[Put Aircon Schedule Request]\nUser Account:{g.account}\nUUID:{g.uuid}\n"
        )
        # Edit schedule
        args = self.put_parser.parse_args()
        app.apscheduler.modify_job(
            id=args["schedule_id"], next_run_time=args["time"], args=[args["action"]]
        )
        return make_response(jsonify({"status": "success"}))

    @auth.login_required
    def delete(self):
        logging.info(
            f"[Put Aircon Schedule Request]\nUser Account:{g.account}\nUUID:{g.uuid}\n"
        )
        # Remove schedule
        args = self.delete_parser.parse_args()
        app.apscheduler.remove_job(args["schedule_id"])
        return make_response(jsonify({"status": "success"}))
