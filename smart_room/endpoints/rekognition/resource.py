import os.path
import time
import glob

from flask import jsonify, current_app as app
from flask_restful import Resource
from loguru import logger
import boto3

from utils.oauth import auth, g
from .model import Rekognition


class RekognitionResource(Resource):
    @auth.login_required
    def get(self):
        logger.info(
            f"[Get Rekognition Request]\nUser Account:{g.account}\nUUID:{g.uuid}\n"
        )
        people_count = self.rekognition()
        response = jsonify({"people_count": people_count})
        return response

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
        logger.info(
            f"[AWS Rekognition Result]\nImage:{os.path.basename(photo)}\nPeople Count:{people_count}\n"
        )
        # Save to DB
        data = {
            "image": os.path.basename(photo),
            "people_count": people_count,
            "rekognition_data": str(labels),
            "user_id": g.uuid,
        }
        Rekognition(**data).add()
        return people_count

    @staticmethod
    def detect_labels_local_file(photo):
        # Rekognition API
        client = boto3.client("rekognition")
        with open(photo, "rb") as image:
            response = client.detect_labels(Image={"Bytes": image.read()})
        return response
