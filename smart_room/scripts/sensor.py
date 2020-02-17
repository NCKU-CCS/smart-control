import os

import time

import logging
import requests

from dotenv import load_dotenv
import RPi.GPIO as GPIO


load_dotenv()

logging.basicConfig(
    level=logging.DEBUG,
    format="[%(levelname)s] - %(asctime)s\n%(message)s\n" + ("-" * 70),
    datefmt="%Y-%m-%dT%H:%M:%S",
)


REKOGNITION_URL = os.environ.get("REKOGNITION_URL", "http://localhost:5000/rekognition")
TOKEN = os.environ.get("TOKEN")


class MotionDetect:
    def __init__(self, pir):
        self.pir = pir
        self.detect()

    def detect(self):
        # Calculate numbers of motion
        counter_motion = 0
        counter_nobody = 0
        try:
            while True:
                # Detected if pir is high
                if GPIO.input(self.pir) == True:
                    logging.info("Motion Detected!")
                    counter_motion += 1
                    counter_nobody = 0
                else:
                    logging.info("Nobody...")
                    counter_motion = 0
                    counter_nobody += 1
                logging.info(
                    f"Detect count: {counter_motion}\nNobody count: {counter_nobody}"
                )

                if counter_motion >= 3:
                    # Calculate People
                    message = requests.get(
                        REKOGNITION_URL, headers={"Authorization": f"Bearer {TOKEN}"}
                    ).json()
                    logging.info(f"[Rekognition Result]\n{message}\n")
                    # Reset Counter
                    counter_motion = 0
                    counter_nobody = 0

                # Future work
                elif counter_nobody >= 20:
                    # No people come in
                    pass

                time.sleep(1)

        except KeyboardInterrupt:
            pass

        finally:
            # reset all GPIO
            GPIO.cleanup()
            logging.info("Program ended")


def main():
    # Assign pins
    pir = int(os.environ.get("PIR_PIN", "8"))
    # Set GPIO to pin numbering
    GPIO.setmode(GPIO.BOARD)
    # Setup GPIO pin PIR as input
    GPIO.setup(pir, GPIO.IN)
    logging.info(f"PIR Sensor initializing on pin {pir}")
    # Start up sensor
    time.sleep(2)
    logging.info("Active")
    logging.info("Press Ctrl+c to end program")
    MotionDetect(pir)


if __name__ == "__main__":
    main()
