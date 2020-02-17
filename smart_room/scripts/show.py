#!/usr/bin/python

import os
import glob
import time
import json
import logging
import requests
from datetime import datetime, timedelta
# tkinter
from tkinter import *
import tkinter.font as tkFont
from PIL import Image, ImageTk

from dotenv import load_dotenv
import RPi.GPIO as GPIO


load_dotenv()

logging.basicConfig(
    level=logging.DEBUG,
    format="[%(levelname)s] - %(asctime)s\n%(message)s\n" + ("-" * 70),
    datefmt="%Y-%m-%dT%H:%M:%S",
)


REKOGNITION_URL = os.environ.get("REKOGNITION_URL", "http://localhost:5000/rekognition")
AIRCON_URL = os.environ.get("AIRCON_URL", "http://localhost:5000/aircon")
CAPTURE_PATH = os.environ.get("CAPTURE_PATH")
TOKEN = os.environ.get("TOKEN")
NCKU_IMG = os.environ.get("NCKU_IMG")
NETDB_IMG = os.environ.get("NETDB_IMG")


class MotionDetect:
    def __init__(self, pir):
        self.pir = pir
        self.aircon_temperature = ""
        self.nobody_counter = 0
        self.rek_people = 0
        self.rek_time = ""
        self.photo = ""
        self.tk_root = Tk()
        self.gui_init()
        self.detect()
        self.tk_root.mainloop()

    def gui_init(self):
        self.tk_root.title('Smart Control')
        # Create Frames
        frm_status = Frame(self.tk_root)
        frm_status.pack(side='left')
        frm_image = Frame(self.tk_root)
        frm_image.pack(side='right')
        # Insert Labels into Status Frame
        head_font = tkFont.Font(family="Lucida Grande", size=30)
        Label(frm_status, text="Smart Control DEMO", font=head_font).pack()
        font_style = tkFont.Font(family="Lucida Grande", size=20)
        self.label_aircon = Label(frm_status, text="Aircon: off", anchor=NW, font=font_style, width=30)
        self.label_aircon.pack()
        self.label_nobody_counter = Label(frm_status, text="Nobody Timer: ", anchor=NW, font=font_style, width=30)
        self.label_nobody_counter.pack()
        self.label_rek_people = Label(frm_status, text="People Count: ", anchor=NW, font=font_style, width=30)
        self.label_rek_people.pack()
        self.label_rek_time = Label(frm_status, text="Rekognition Time: ", anchor=NW, font=font_style, width=30)
        self.label_rek_time.pack()
        self.label_time = Label(frm_status, text="", anchor=NW, font=font_style, width=30)
        self.label_time.pack()
        # Netdb
        frm_netdb = Frame(frm_status)
        frm_netdb.pack()
        self.ncku_img = ImageTk.PhotoImage(Image.open(NCKU_IMG).resize((60, 60)))
        Label(frm_netdb, image=self.ncku_img, width=60, height=60).pack(side=LEFT)
        Label(frm_netdb, text="NCKU NETDB", font=head_font).pack(side=LEFT)
        self.netdb_img = ImageTk.PhotoImage(Image.open(NETDB_IMG).resize((60, 60)))
        Label(frm_netdb, image=self.netdb_img, width=60, height=60).pack(side=LEFT)
        # Insert Labels into Image Frame
        self.canvas = Canvas(frm_image, width=450, height=300)
        self.canvas.pack()
        photo_path = glob.glob(CAPTURE_PATH)
        self.img = ImageTk.PhotoImage(Image.open(photo_path[0]).resize((450, 300)))
        self.tk_root.update_idletasks()
        self.tk_root.update()
        # self.tk_root.mainloop()

    def detect(self):
        # Calculate numbers of motion
        counter_motion = 0
        self.nobody_counter = 0
        try:
            while True:
                # Detected if pir is high
                if GPIO.input(self.pir) == True:
                    logging.info("Motion Detected!")
                    counter_motion += 1
                    self.nobody_counter = 0
                else:
                    logging.info("Nobody...")
                    counter_motion = 0
                    self.nobody_counter += 1
                logging.info(
                    f"Detect count: {counter_motion}\nNobody count: {self.nobody_counter}"
                )

                if counter_motion >= 2:
                    # People Rekognition
                    self.rekognition()
                    # Reset Counter
                    counter_motion = 0
                    self.nobody_counter = 0

                # No people come in for half an hour
                elif self.nobody_counter >= 1800:
                    # if rekogmition no people then trun off aircon
                    if self.rekognition() == 0:
                        self.aircon('off')
                    else:
                        self.nobody_counter = 0

                # update datas
                if self.nobody_counter == 0:
                    motion_status = "Motion Detected!"
                else:
                    motion_status = str(timedelta(seconds=self.nobody_counter))
                self.label_nobody_counter.config(text=f"Nobody Timer: {motion_status}")
                self.label_time.config(text=datetime.now().strftime("Clock: %Y-%m-%d %H:%M:%S"))
                self.refresh_image()
                self.tk_root.update_idletasks()
                self.tk_root.update()
                # update every minutes
                time.sleep(1)

        except KeyboardInterrupt:
            pass

        finally:
            # reset all GPIO
            GPIO.cleanup()
            logging.info("Program ended")

    def rekognition(self):
        # Record time
        time_now = datetime.now().strftime("%Y-%m-%d %H:%M")
        # Pictore takes one per minutes
        # Rekognition result will be same in one minutes
        if time_now == self.rek_time:
            return self.rek_people
        # Rekognition API
        try:
            message = requests.get(
                REKOGNITION_URL, headers={"Authorization": f"Bearer {TOKEN}"}
            ).json()
            logging.info(f"[Rekognition Result]\n{message}\n")
            self.aircon_control(message['people_count'])
            self.rek_people = int(message['people_count'])
            self.rek_time = time_now
            self.label_rek_people.config(text=f"People Count: {self.rek_people}")
            self.label_rek_time.config(text=f"Rekognition Time: {self.rek_time}")
        except:
            pass
        return self.rek_people

    def aircon_control(self, people_now):
        # control aircon logic
        if people_now > 0 and self.rek_people == 0:
            self.aircon('25c')

    def aircon(self, command):
        # Aircon API
        try:
            message = requests.post(
                AIRCON_URL,
                headers={"Authorization": f"Bearer {TOKEN}", "Content-Type": "application/json"},
                data=json.dumps({"action": command})
            ).json()
            logging.info(f"[Aircon]\nset to: {command}\n")
            if message['status'] == "success":
                self.aircon_temperature = command
                self.label_aircon.config(text=f"Aircon: {self.aircon_temperature}")
                return True
        except:
            pass
        return False

    def refresh_image(self):
        photo_path = glob.glob(CAPTURE_PATH)
        if photo_path and photo_path[0] != self.photo:
            self.img = ImageTk.PhotoImage(Image.open(photo_path[0]).resize((500, 300)))
            self.photo = photo_path[0]
        self.canvas.create_image(0, 0, anchor=NW, image=self.img)


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
