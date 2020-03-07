import os
import smbus
import glob
import time
import json
from loguru import logger
import requests
from datetime import datetime, timedelta
from tkinter import Tk, Frame, Label, Canvas, Toplevel, Button, StringVar, Entry
from tkinter.ttk import Notebook, Combobox
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
        self.indoor_di_c = 0
        self.indoor_di_f = 0
        self.indoor_di_cond = ""
        self.hue_light = "off"
        self.nobody_counter = 0
        self.rek_people = 0
        self.rek_time = ""
        self.photo = ""
        self.bridge = Bridge(BRIDGE_IP)
        self.bridge.connect()
        # GUI
        self.tk_root = Tk()
        self.notebook = Notebook()
        # Information frame
        self.information_frame = None
        self.label_temperature = None
        self.label_humidity = None
        self.label_luminance = None
        self.label_di = None
        self.label_hue_light = None
        self.label_aircon = None
        self.label_nobody_counter = None
        self.label_time = None
        self.ncku_img = None
        self.netdb_img = None
        self.canvas = None
        self.img = None
        self.label_rek_people = None
        self.label_rek_time = None
        # Schedule frame
        self.schedule_frame = None
        # DR frame
        self.dr_frame = None
        # GUI Init
        self.gui_init()
        self.detect()
        self.tk_root.mainloop()

    def gui_init(self):
        self.tk_root.title("Smart Control")
        # Create Frames
        self.information_init()
        self.schedule_init()
        self.dr_init()

    def information_init(self):
        # Information Frame
        self.information_frame = Frame()
        frm_status = Frame(self.information_frame)
        frm_status.pack(side="left")
        frm_image = Frame(self.information_frame)
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
        self.label_di = Label(
            frm_status, text="DI: ", anchor="nw", font=font_style, width=30
        )
        self.label_di.pack()
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
        self.notebook.add(self.information_frame, text="Information")
        self.notebook.pack()

    def schedule_init(self):
        self.schedule_frame = Frame()
        self.notebook.add(self.schedule_frame, text="Schedule")
        self.notebook.pack()

    def dr_init(self):
        self.dr_frame = Frame()
        self.notebook.add(self.dr_frame, text="Demand Response")
        self.notebook.pack()

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
                dht_humidity, dht_temperature = Adafruit_DHT.read(
                    Adafruit_DHT.AM2302, 27
                )
                if dht_humidity and dht_temperature:
                    self.indoor_humidity, self.indoor_temperature = (
                        dht_humidity,
                        dht_temperature,
                    )
                    self.calculate_di()
                    self.generate_condition()
                self.label_humidity.config(
                    text=f"Humidity: {format(self.indoor_humidity, '.1f')} %"
                )
                self.label_temperature.config(
                    text=f"Temperature: {format(self.indoor_temperature, '.1f')} °C"
                )
                self.label_di.config(text=f"DI: {format(self.indoor_di_c, '.1f')} °C, {self.indoor_di_cond}")
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

    def calculate_di(self):
        temperature_fahrenheit = self.indoor_temperature * 1.8 + 32
        self.indoor_di_f = temperature_fahrenheit - 0.55 * (
            1 - self.indoor_luminance / 100
        ) * (temperature_fahrenheit - 58)
        self.indoor_di_c = self.fahrenheit_to_celsius(self.indoor_di_f)

    @staticmethod
    def fahrenheit_to_celsius(fahrenheit):
        return (fahrenheit - 32) / 1.8

    def generate_condition(self):
        if self.indoor_di_f <= 70:
            self.indoor_di_cond = "Comfortable"
        elif 70 < self.indoor_di_f <= 75:
            self.indoor_di_cond = "Slightly Warm"
        elif 75 < self.indoor_di_f <= 80:
            self.indoor_di_cond = "Warm"
        elif 80 < self.indoor_di_f <= 85:
            self.indoor_di_cond = "Hot"
        elif self.indoor_di_f > 85:
            self.indoor_di_cond = "Very Hot"

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
