import os.path
import glob
import time

from flask import jsonify, current_app as app
from flask_restful import Resource
import boto3

from utils.logging import logging
from utils.oauth import auth, g
from .model import Rekognition


class RekognitionResource(Resource):
    # pylint: disable=R0201
    @auth.login_required
    def get(self):
        logging.info(
            f"[Get Rekognition Request]\nUser Account:{g.account}\nUUID:{g.uuid}\n"
        )
        people_count = self.rekognition()
        response = jsonify({"people_count": people_count})
        return response

    # pylint: enable=R0201

    def rekognition(self):
        # Catch the newest picture
        # Prevent when old picture has been delete but new picture haven't save.
        while not glob.glob(app.config["CAPTURE_PATH"]):
            time.sleep(1)
        photo = glob.glob(app.config["CAPTURE_PATH"])[0]
        labels = self.detect_labels_local_file(photo)
        people_count = [
            len(label["Instances"])
            for label in labels["Labels"]
            if label["Name"] == "Person"
        ]
        people_count = people_count[0] if people_count else 0
        logging.info(
            f"[AWS Rekognition Result]\nImage:{os.path.basename(photo)}\nPeople Count:{people_count}\n"
        )
        # Save to DB
        data = {
            "image": os.path.basename(photo),
            "people_count": people_count,
            "rekognition_data": str(labels),
            "user_id": g.uuid,
        }
        Rekognition.add(Rekognition(**data))
        return people_count

    # pylint: disable=R0201
    def detect_labels_local_file(self, photo):
        # To disable lots of DEBUG message from boto3 and AWS service
        logging.disable(logging.DEBUG)
        # Rekognition API
        client = boto3.client("rekognition")
        with open(photo, "rb") as image:
            response = client.detect_labels(Image={"Bytes": image.read()})
        # Enable all Logs
        logging.disable(logging.NOTSET)
        return response

    # pylint: enable=R0201
