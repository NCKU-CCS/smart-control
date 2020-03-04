import os
import smbus
import glob
import time
import json
from loguru import logger
import requests
from datetime import datetime, timedelta
from tkinter import Tk, Frame, Label, Canvas
import tkinter.font as tkFont

import RPi.GPIO as GPIO

import Adafruit_DHT
from PIL import Image, ImageTk
from dotenv import load_dotenv
from phue import Bridge


load_dotenv()


REKOGNITION_URL = os.environ.get("REKOGNITION_URL", "http://localhost:5000/rekognition")
AIRCON_URL = os.environ.get("AIRCON_URL", "http://localhost:5000/aircon")
CAPTURE_PATH = os.environ.get("CAPTURE_PATH")
TOKEN = os.environ.get("TOKEN")
NCKU_IMG = os.environ.get("NCKU_IMG")
NETDB_IMG = os.environ.get("NETDB_IMG")
BRIDGE_IP = os.environ.get("BRIDGE_IP", "192.168.1.90")
DEVICE = 0x23
ONE_TIME_HIGH_RES_MODE_1 = 0x20
BUS = smbus.SMBus(1)


class MotionDetect:
    def __init__(self, pir):
        self.pir = pir
        self.aircon_temperature = ""
        self.indoor_temperature = 0
        self.indoor_humidity = 0
        self.indoor_luminance = 0
        self.hue_light = "off"
        self.nobody_counter = 0
        self.rek_people = 0
        self.rek_time = ""
        self.photo = ""
        self.bridge = Bridge(BRIDGE_IP)
        self.bridge.connect()
        self.tk_root = Tk()
        self.gui_init()
        self.detect()
        self.tk_root.mainloop()

    def gui_init(self):
        self.tk_root.title("Smart Control")
        # Create Frames
        frm_status = Frame(self.tk_root)
        frm_status.pack(side="left")
        frm_image = Frame(self.tk_root)
        frm_image.pack(side="right")
        # Insert Labels into Status Frame
        head_font = tkFont.Font(family="Lucida Grande", size=30)
        Label(frm_status, text="Smart Control DEMO", font=head_font).pack()
        font_style = tkFont.Font(family="Lucida Grande", size=20)
        # Sensors
        self.label_temperature = Label(
            frm_status, text="Temperature: ", anchor="nw", font=font_style, width=30
        )
        self.label_temperature.pack()
        self.label_humidity = Label(
            frm_status, text="Humidity: ", anchor="nw", font=font_style, width=30
        )
        self.label_humidity.pack()
        self.label_luminance = Label(
            frm_status, text="Luminance: ", anchor="nw", font=font_style, width=30
        )
        self.label_luminance.pack()
        # Controller
        self.label_hue_light = Label(
            frm_status, text="Light Bar: off", anchor="nw", font=font_style, width=30
        )
        self.label_hue_light.pack()
        self.label_aircon = Label(
            frm_status,
            text="Aircon: Front: off\tBack: off",
            anchor="nw",
            font=font_style,
            width=30,
        )
        self.label_aircon.pack()
        self.label_nobody_counter = Label(
            frm_status, text="Nobody Timer: ", anchor="nw", font=font_style, width=30
        )
        self.label_nobody_counter.pack()
        self.label_time = Label(
            frm_status, text="", anchor="nw", font=font_style, width=30
        )
        self.label_time.pack()
        # Netdb
        frm_netdb = Frame(frm_status)
        frm_netdb.pack()
        self.ncku_img = ImageTk.PhotoImage(Image.open(NCKU_IMG).resize((60, 60)))
        Label(frm_netdb, image=self.ncku_img, width=60, height=60).pack(side="left")
        Label(frm_netdb, text="NCKU NETDB", font=head_font).pack(side="left")
        self.netdb_img = ImageTk.PhotoImage(Image.open(NETDB_IMG).resize((60, 60)))
        Label(frm_netdb, image=self.netdb_img, width=60, height=60).pack(side="left")
        # Insert Labels into Image Frame
        self.canvas = Canvas(frm_image, width=450, height=300)
        self.canvas.pack()
        photo_path = glob.glob(CAPTURE_PATH)
        self.img = ImageTk.PhotoImage(Image.open(photo_path[0]).resize((450, 300)))
        self.tk_root.update_idletasks()
        self.tk_root.update()
        # Recognition info
        # Label(frm_image, text="Last Recognition Info", font=font_style, width=30).pack()
        self.label_rek_people = Label(
            frm_image, text="People Count: ", anchor="nw", font=font_style, width=30
        )
        self.label_rek_people.pack()
        self.label_rek_time = Label(
            frm_image, text="Recognition Time: ", anchor="nw", font=font_style, width=30
        )
        self.label_rek_time.pack()

    def detect(self):
        # Calculate numbers of motion
        counter_motion = 0
        self.nobody_counter = 0
        try:
            while True:
                # Detected if pir is high
                if GPIO.input(self.pir) == True:
                    logger.info("Motion Detected!")
                    counter_motion += 1
                    self.nobody_counter = 0
                else:
                    logger.info("Nobody...")
                    counter_motion = 0
                    self.nobody_counter += 1
                logger.info(
                    f"Detect count: {counter_motion}\tNobody count: {self.nobody_counter}"
                )

                if counter_motion >= 2:
                    # People Rekognition
                    people_count = self.rekognition()
                    if people_count != 0:
                        self.set_light(100)
                    # Reset Counter
                    counter_motion = 0
                    self.nobody_counter = 0

                # No people come in for 5 minutes: turn light to 50%
                elif self.nobody_counter == 300:
                    if self.rekognition() == 0:
                        self.set_light(50)
                    else:
                        self.nobody_counter = 0

                # No people come in for 20 minutes: turn off light and aircon
                elif self.nobody_counter >= 600:
                    if self.rekognition() == 0:
                        self.aircon("off")
                        self.set_light(0)
                    else:
                        self.nobody_counter = 0

                # update sensor
                self.indoor_luminance = self.read_light()
                self.label_luminance.config(
                    text=f"Luminance: {format(self.indoor_luminance, '.1f')} lux"
                )
                self.indoor_humidity, self.indoor_temperature = Adafruit_DHT.read_retry(
                    Adafruit_DHT.AM2302, 27
                )
                self.label_humidity.config(
                    text=f"Humidity: {format(self.indoor_humidity, '.1f')} %"
                )
                self.label_temperature.config(
                    text=f"Temperature: {format(self.indoor_temperature, '.1f')} °C"
                )
                self.label_hue_light.config(text=f"Light Bar: {self.hue_light}")
                # update datas
                if self.nobody_counter == 0:
                    motion_status = "Motion Detected!"
                else:
                    motion_status = str(timedelta(seconds=self.nobody_counter))
                self.label_nobody_counter.config(text=f"Nobody Timer: {motion_status}")
                self.label_time.config(
                    text=datetime.now().strftime("Clock: %Y-%m-%d %H:%M:%S")
                )
                self.refresh_image()
                self.tk_root.update_idletasks()
                self.tk_root.update()
                # update every minutes
                time.sleep(0.5)

        except KeyboardInterrupt:
            pass

        finally:
            # reset all GPIO
            GPIO.cleanup()
            logger.info("Program ended")

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
            logger.info(f"[Rekognition Result]\n{message}\n")
            # move this to detect()
            self.aircon_control(message["people_count"])
            self.rek_people = int(message["people_count"])
            self.rek_time = time_now
            self.label_rek_people.config(text=f"People Count: {self.rek_people}")
            self.label_rek_time.config(text=f"Recognition Time: {self.rek_time}")
        except:
            pass
        return self.rek_people

    def aircon_control(self, people_now):
        # control aircon logic
        if people_now > 0 and self.rek_people == 0:
            self.aircon("25c")

    def aircon(self, command):
        # Aircon API
        try:
            message = requests.post(
                AIRCON_URL,
                headers={
                    "Authorization": f"Bearer {TOKEN}",
                    "Content-Type": "application/json",
                },
                data=json.dumps({"action": command}),
            ).json()
            logger.info(f"[Aircon]\nset to: {command}\n")
            if message["status"] == "success":
                self.aircon_temperature = command
                self.label_aircon.config(
                    text=f"Aircon: Front:{self.aircon_temperature}\tBack: {self.aircon_temperature}"
                )
                return True
        except:
            pass
        return False

    def refresh_image(self):
        photo_path = glob.glob(CAPTURE_PATH)
        if photo_path and photo_path[0] != self.photo:
            self.img = ImageTk.PhotoImage(Image.open(photo_path[0]).resize((500, 300)))
            self.photo = photo_path[0]
        self.canvas.create_image(0, 0, anchor="nw", image=self.img)

    def bytes_to_number(self, data):
        # Simple function to convert 2 bytes of data
        # into a decimal number. Optional parameter 'decimals'
        # will round to specified number of decimal places.
        result = (data[1] + (256 * data[0])) / 1.2
        return result

    def read_light(self, addr=DEVICE):
        # Read data from I2C interface
        data = BUS.read_i2c_block_data(addr, ONE_TIME_HIGH_RES_MODE_1)
        return self.bytes_to_number(data)

    def set_light(self, brightness):
        if brightness == 0:
            self.bridge.set_light(1, "on", False)
            self.hue_light = "off"
        else:
            self.bridge.set_light(1, "on", True)
            self.bridge.set_light(1, "bri", int(brightness * 255 / 100))
            self.hue_light = f"{brightness} %"
        logger.info(f"[Hue Light Bar] set to {brightness}")


def main():
    # Assign pins
    pir = int(os.environ.get("PIR_PIN", "8"))
    # Set GPIO to pin numbering
    GPIO.setmode(GPIO.BOARD)
    # Setup GPIO pin PIR as input
    GPIO.setup(pir, GPIO.IN)
    logger.info(f"PIR Sensor initializing on pin {pir}")
    # Start up sensor
    time.sleep(2)
    logger.info("Active")
    logger.info("Press Ctrl+c to end program")
    MotionDetect(pir)


if __name__ == "__main__":
    main()
