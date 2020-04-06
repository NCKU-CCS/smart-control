import os
import smbus
import glob
import time
import json
from loguru import logger
import requests
from datetime import datetime, timedelta
import uuid

from tkinter import Tk, Frame, Label, Canvas, Toplevel, Button, StringVar, Entry, Listbox, Scrollbar, ttk
from tkinter.ttk import Notebook, Combobox
import tkinter.font as tkFont

import RPi.GPIO as GPIO

import Adafruit_DHT
from PIL import Image, ImageTk
from dotenv import load_dotenv
from phue import Bridge
from tkcalendar import Calendar
from apscheduler.schedulers.background import BackgroundScheduler

load_dotenv()


REKOGNITION_URL = os.environ.get("REKOGNITION_URL", "http://localhost:5000/rekognition")
AIRCON_URL = os.environ.get("AIRCON_URL", "http://localhost:5000/aircon")
CAPTURE_PATH = os.environ.get("CAPTURE_PATH")
TOKEN = os.environ.get("TOKEN")
NCKU_IMG = os.environ.get("NCKU_IMG")
NETDB_IMG = os.environ.get("NETDB_IMG")
BRIDGE_IP = os.environ.get("BRIDGE_IP", "192.168.1.5")
DEVICE = 0x23
ONE_TIME_HIGH_RES_MODE_1 = 0x20
BUS = smbus.SMBus(1)
SCHEDULE_URL = os.environ.get("SCHEDULE_URL", "http://192.168.1.7:5000/schedule")
HEADER = {"Authorization": f"Bearer {TOKEN}"}
scheduler = BackgroundScheduler()
scheduler.start()

class MotionDetect:
    def __init__(self, pir):
        self.pir = pir
        self.aircon_temperature_front = "off"
        self.aircon_temperature_back = "off"
        self.indoor_temperature = 0
        self.indoor_humidity = 0
        self.indoor_luminance = 0
        self.indoor_di = 0
        self.indoor_di_cond = ""
        self.hue_light_front = "off"
        self.hue_light_back = "off"
        self.nobody_counter = 0
        self.rek_people = 0
        self.rek_time = ""
        self.photo = ""
        self.bridge = Bridge(BRIDGE_IP)
        self.bridge.connect()
        # GUI
        self.tk_root = Tk()
        self.notebook = Notebook()
        self.head_font = None
        self.subhead_font = None
        self.body_font = None
        self.list_font = tkFont.Font(family="Lucida Grande", size=16)
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
        self.list_schedule = []
        # Schedule frame
        self.schedule_frame = None
        # DR frame
        self.dr_frame = None
        self.normal_setting = {}
        # GUI Init
        self.gui_init()
        self.notebook.pack()
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
        self.information_frame = Frame(bg="#F2F2F2")
        frm_status = Frame(self.information_frame, bg="#F2F2F2")
        frm_status.pack(side="left")
        frm_image = Frame(self.information_frame, bg="#F2F2F2")
        frm_image.pack(side="right")
        # Insert Labels into Status Frame
        self.head_font = tkFont.Font(family="Lucida Grande", size=30)
        self.subhead_font = tkFont.Font(family="Lucida Grande", size=24)
        Label(frm_status, text="Smart Control DEMO", font=self.head_font, fg="#333333", bg="#F2F2F2").pack()
        self.body_font = tkFont.Font(family="Lucida Grande", size=20)
        # Sensors
        self.label_temperature = Label(
            frm_status, text="Temperature: ", anchor="nw", font=self.body_font, width=30, fg="#333333", bg="#F2F2F2"
        )
        self.label_temperature.pack()
        self.label_humidity = Label(
            frm_status, text="Humidity: ", anchor="nw", font=self.body_font, width=30, fg="#333333", bg="#F2F2F2"
        )
        self.label_humidity.pack()
        self.label_luminance = Label(
            frm_status, text="Luminance: ", anchor="nw", font=self.body_font, width=30, fg="#333333", bg="#F2F2F2"
        )
        self.label_luminance.pack()
        self.label_di = Label(
            frm_status, text="DI: ", anchor="nw", font=self.body_font, width=30, fg="#333333", bg="#F2F2F2"
        )
        self.label_di.pack()
        # Controller
        self.label_hue_light = Label(
            frm_status, text="Light Bar: Front: off\tBack: off", anchor="nw", font=self.body_font, width=30, fg="#333333", bg="#F2F2F2"
        )
        self.label_hue_light.pack()
        self.label_aircon = Label(
            frm_status,
            text="Aircon: Front: off\tBack: off",
            anchor="nw",
            font=self.body_font,
            width=30,
            fg="#333333", bg="#F2F2F2",
        )
        self.label_aircon.pack()
        self.label_nobody_counter = Label(
            frm_status, text="Nobody Timer: ", anchor="nw", font=self.body_font, width=30, fg="#333333", bg="#F2F2F2"
        )
        self.label_nobody_counter.pack()
        self.label_time = Label(
            frm_status, text="", anchor="nw", font=self.body_font, width=30, fg="#333333", bg="#F2F2F2"
        )
        self.label_time.pack()
        # Netdb
        frm_netdb = Frame(frm_status, bg="#F2F2F2")
        frm_netdb.pack()
        self.ncku_img = ImageTk.PhotoImage(Image.open(NCKU_IMG).resize((60, 60)))
        Label(frm_netdb, image=self.ncku_img, width=60, height=60, fg="#333333", bg="#F2F2F2").pack(side="left")
        Label(frm_netdb, text="NCKU NETDB", font=self.head_font, fg="#333333", bg="#F2F2F2").pack(side="left")
        self.netdb_img = ImageTk.PhotoImage(Image.open(NETDB_IMG).resize((60, 60)))
        Label(frm_netdb, image=self.netdb_img, width=60, height=60, fg="#333333", bg="#F2F2F2").pack(side="left")
        # Insert Labels into Image Frame
        self.lbl_info_status = Label(frm_image, text="", font=self.body_font, fg="#333333", bg="#F2F2F2")
        self.lbl_info_status.pack()
        self.canvas = Canvas(frm_image, width=450, height=300)
        self.canvas.pack()
        photo_path = glob.glob(CAPTURE_PATH)
        self.img = ImageTk.PhotoImage(Image.open(photo_path[0]).resize((450, 300)))
        self.tk_root.update_idletasks()
        self.tk_root.update()
        # Recognition info
        self.label_rek_people = Label(
            frm_image, text="People Count: ", anchor="nw", font=self.body_font, width=30, fg="#333333", bg="#F2F2F2"
        )
        self.label_rek_people.pack()
        self.label_rek_time = Label(
            frm_image, text="Recognition Time: ", anchor="nw", font=self.body_font, width=30, fg="#333333", bg="#F2F2F2"
        )
        self.label_rek_time.pack()
        self.notebook.add(self.information_frame, text="Information")

    @staticmethod
    def send_schedule(payload):
        response = requests.post(SCHEDULE_URL, headers=HEADER, json=payload).json()
        logger.info(response)

    def pop_calendar(self, save_date):
        def get_select():
            save_date.set(cal.selection_get().strftime("%Y-%m-%d"))
            top.destroy()

        top = Toplevel(self.tk_root)
        cal = Calendar(
            top,
            font="Arial 14",
            selectmode="day",
            mindate=datetime.today(),
            showweeknumbers=False,
            year=datetime.today().year,
            month=datetime.today().month,
            day=datetime.today().day,
            foreground="black",
            background="white",
            selectforeground="blue",
        )

        cal.pack(fill="both", expand=True)
        Button(top, text="ok", command=get_select).pack()

    def get_action(self):
        action_time = f"{self.pickdate.get()} {self.combo_pickhour.get()}:{self.combo_pickmin.get()}:0"
        action_set = {
            "light_front": self.schedule_set_light_front.get(),
            "light_back": self.schedule_set_light_back.get(),
            "aircon_front": self.combo_aircon_front.get(),
            "aircon_back": self.combo_aircon_back.get(),
        }
        payload = {"action": action_set, "time": action_time}
        self.send_schedule(payload)
        self.get_schedule()
        # add to local scheduler
        if action_set["aircon_front"] == "keep":
            action_set["aircon_front"] = self.aircon_temperature_front
        if action_set["aircon_back"] == "keep":
            action_set["aircon_back"] = self.aircon_temperature_back
        scheduler.add_job(
            func=self.update_setting,
            trigger="date",
            run_date=datetime.strptime(action_time, "%Y-%m-%d %H:%M:%S"),
            args=[action_set["light_front"], action_set["light_back"], action_set["aircon_front"], action_set["aircon_back"]],
            id=str(uuid.uuid4()),
        )

    def schedule_init(self):
        self.schedule_frame = Frame(bg="#F2F2F2")
        self.notebook.add(self.schedule_frame, text="Schedule")
        Label(self.schedule_frame, text="Appliance Scheduling", font=self.head_font, fg="#333333", bg="#F2F2F2").pack()
        frm_schedule = Frame(self.schedule_frame, bg="#F2F2F2")
        frm_schedule.pack()
        frm_schedule_insert = Frame(frm_schedule, bg="#F2F2F2")
        frm_schedule_insert.pack(side="left", padx=30)
        frm_schedule_all = Frame(frm_schedule, bg="#F2F2F2")
        frm_schedule_all.pack(side="right", padx=30)
        # Schedule Insert
        Label(frm_schedule_insert, text="Add Schedule", font=self.subhead_font, fg="#333333", bg="#F2F2F2").pack()
        # Pickup date frame
        self.frame_date = Frame(frm_schedule_insert, bg="#F2F2F2")
        self.frame_date.pack()

        self.pickdate = StringVar()
        self.entry_pickdate = Entry(self.frame_date, width=10, textvariable=self.pickdate, font=self.body_font)
        self.entry_pickdate.bind("<Button-1>", lambda x: self.pop_calendar(self.pickdate))
        self.entry_pickdate.grid(row=0, column=0)
        self.pickdate.set(datetime.today().strftime("%Y-%m-%d"))

        # pick time
        self.combo_pickhour = Combobox(self.frame_date, values=[i for i in range(25)], width=3, font=self.body_font)
        self.combo_pickhour.grid(row=0, column=1)
        self.combo_pickhour.current(datetime.today().hour)

        Label(self.frame_date, text=":", font=self.body_font, fg="#333333", bg="#F2F2F2").grid(row=0, column=2)

        self.combo_pickmin = Combobox(self.frame_date, values=[i for i in range(60)], width=3, font=self.body_font)
        self.combo_pickmin.grid(row=0, column=3)
        self.combo_pickmin.current(datetime.today().minute)

        # set action
        self.frame_action = Frame(frm_schedule_insert, bg="#F2F2F2")
        self.frame_action.pack()
        Label(self.frame_action, text="Light Front", font=self.body_font, fg="#333333", bg="#F2F2F2").grid(row=0, column=0)
        self.schedule_set_light_front = StringVar()
        self.entry_light_front = Entry(self.frame_action, width=5, textvariable=self.schedule_set_light_front, font=self.body_font)
        self.schedule_set_light_front.set("100")
        self.entry_light_front.grid(row=0, column=1)
        Label(self.frame_action, text="%", font=self.body_font, fg="#333333", bg="#F2F2F2").grid(row=0, column=2)
        Label(self.frame_action, text="Light Back", font=self.body_font, fg="#333333", bg="#F2F2F2").grid(row=1, column=0)
        self.schedule_set_light_back = StringVar()
        self.entry_light_back = Entry(self.frame_action, width=5, textvariable=self.schedule_set_light_back, font=self.body_font)
        self.schedule_set_light_back.set("100")
        self.entry_light_back.grid(row=1, column=1)
        Label(self.frame_action, text="%", font=self.body_font, fg="#333333", bg="#F2F2F2").grid(row=1, column=2)
        # Aircon
        self.list_aircon = ["keep", "off"]
        self.list_aircon += [f"{i}c" for i in range(16, 31)]
        Label(self.frame_action, text="Aircon Front", font=self.body_font, fg="#333333", bg="#F2F2F2").grid(row=2, column=0)
        self.combo_aircon_front = Combobox(
            self.frame_action, values=self.list_aircon, width=5, state="readonly", font=self.body_font
        )
        self.combo_aircon_front.current(0)
        self.combo_aircon_front.grid(row=2, column=1)
        Label(self.frame_action, text="Aircon Back", font=self.body_font, fg="#333333", bg="#F2F2F2").grid(row=3, column=0)
        self.combo_aircon_back = Combobox(
            self.frame_action, values=self.list_aircon, width=5, state="readonly", font=self.body_font
        )
        self.combo_aircon_back.current(0)
        self.combo_aircon_back.grid(row=3, column=1)

        # Add schedule
        Button(frm_schedule_insert, text="Add", command=self.get_action, font=self.body_font).pack()

        Label(frm_schedule_insert, text="", font=self.body_font, fg="#333333", bg="#F2F2F2").pack()
        # Netdb
        frm_netdb = Frame(frm_schedule_insert, bg="#F2F2F2")
        frm_netdb.pack()
        Label(frm_netdb, image=self.ncku_img, width=60, height=60, bg="#F2F2F2").pack(side="left")
        Label(frm_netdb, text="NCKU NETDB", font=self.head_font, fg="#333333", bg="#F2F2F2").pack(side="left")
        Label(frm_netdb, image=self.netdb_img, width=60, height=60, bg="#F2F2F2").pack(side="left")

        # List Schedule
        Label(frm_schedule_all, text="Schedule List", font=self.subhead_font, fg="#333333", bg="#F2F2F2").pack()
        scrollbar = Scrollbar(frm_schedule_all)
        scrollbar.pack(side='right', fill='y')
        self.lb_schedule = Listbox(frm_schedule_all, width=30, height=10, font=self.list_font, yscrollcommand=scrollbar.set)
        self.get_schedule()
        self.lb_schedule.pack(side='left', fill='both', expand=True)
        scrollbar.config(command=self.lb_schedule.yview)

    def dr_init(self):
        self.dr_frame = Frame(bg="#F2F2F2")
        self.notebook.add(self.dr_frame, text="Demand Response")
        Label(self.dr_frame, text="Demand Response Setting", font=self.head_font, fg="#333333", bg="#F2F2F2").pack()
        frm_dr = Frame(self.dr_frame, bg="#F2F2F2")
        frm_dr.pack()
        frm_dr_setting = Frame(frm_dr, bg="#F2F2F2")
        frm_dr_setting.pack(side="left", padx=20)
        frm_dr_schedule = Frame(frm_dr, bg="#F2F2F2")
        frm_dr_schedule.pack(side="right", padx=20)
        Label(frm_dr_setting, text="", fg="#333333", bg="#F2F2F2").pack()
        Label(frm_dr_setting, text="Adjustable value", font=self.subhead_font, fg="#333333", bg="#F2F2F2").pack()
        # Setting Frame
        frm_set_dr = Frame(frm_dr_setting, bg="#F2F2F2")
        frm_set_dr.pack()
        Label(frm_set_dr, text="Light Front", font=self.body_font, fg="#333333", bg="#F2F2F2").grid(row=0, column=0)
        self.combo_dr_bright_front = Combobox(frm_set_dr, values=[i for i in range(5, 50, 5)], width=3, font=self.body_font)
        self.combo_dr_bright_front.grid(row=0, column=1)
        self.combo_dr_bright_front.current(0)
        Label(frm_set_dr, text="%", font=self.body_font, fg="#333333", bg="#F2F2F2").grid(row=0, column=2)
        Label(frm_set_dr, text="Light Back", font=self.body_font, fg="#333333", bg="#F2F2F2").grid(row=1, column=0)
        self.combo_dr_bright_back = Combobox(frm_set_dr, values=[i for i in range(5, 50, 5)], width=3, font=self.body_font)
        self.combo_dr_bright_back.grid(row=1, column=1)
        self.combo_dr_bright_back.current(0)
        Label(frm_set_dr, text="%", font=self.body_font, fg="#333333", bg="#F2F2F2").grid(row=1, column=2)
        Label(frm_set_dr, text="Aircon Front", font=self.body_font, fg="#333333", bg="#F2F2F2").grid(row=2, column=0)
        self.combo_dr_aircon_front = Combobox(frm_set_dr, values=[i for i in range(1, 11)], width=3, font=self.body_font)
        self.combo_dr_aircon_front.grid(row=2, column=1)
        self.combo_dr_aircon_front.current(0)
        Label(frm_set_dr, text="°C", font=self.body_font, fg="#333333", bg="#F2F2F2").grid(row=2, column=2)
        Label(frm_set_dr, text="Aircon Back", font=self.body_font, fg="#333333", bg="#F2F2F2").grid(row=3, column=0)
        self.combo_dr_aircon_back = Combobox(frm_set_dr, values=[i for i in range(1, 11)], width=3, font=self.body_font)
        self.combo_dr_aircon_back.grid(row=3, column=1)
        self.combo_dr_aircon_back.current(0)
        Label(frm_set_dr, text="°C", font=self.body_font, fg="#333333", bg="#F2F2F2").grid(row=3, column=2)
        Label(frm_dr_setting, text="", bg="#F2F2F2").pack()
        # Start and Stop button
        Label(frm_dr_setting, text="Real Time DR", font=self.body_font, fg="#333333", bg="#F2F2F2").pack()
        self.dr_live_state = False
        frm_dr_live = Frame(frm_dr_setting, bg="#F2F2F2")
        frm_dr_live.pack()
        self.btn_dr_start = Button(frm_dr_live, text="Start", font=self.body_font, command=lambda: self.exec_dr("start", self.combo_dr_bright_front.get(), self.combo_dr_bright_back.get(), self.combo_dr_aircon_front.get(), self.combo_dr_aircon_back.get()), state="normal")
        self.btn_dr_start.grid(row=0, column=0)
        self.btn_dr_stop = Button(frm_dr_live, text="Stop", font=self.body_font, command=lambda: self.exec_dr("stop"), state="disable")
        self.btn_dr_stop.grid(row=0, column=1)
        self.dr_live_timer = 0
        self.lbl_dr_timer = Label(frm_dr_live, text="00:00", font=self.body_font, fg="#333333", bg="#F2F2F2")
        self.lbl_dr_timer.grid(row=0, column=2)
        Label(frm_dr_setting, text="", bg="#F2F2F2").pack()
        # Netdb
        frm_netdb = Frame(frm_dr_setting, bg="#F2F2F2")
        frm_netdb.pack()
        Label(frm_netdb, image=self.ncku_img, width=60, height=60, bg="#F2F2F2").pack(side="left")
        Label(frm_netdb, text="NCKU NETDB", font=self.head_font, fg="#333333", bg="#F2F2F2").pack(side="left")
        Label(frm_netdb, image=self.netdb_img, width=60, height=60, bg="#F2F2F2").pack(side="left")
        # Schedule
        Label(frm_dr_schedule, text="Add DR Schedule", font=self.subhead_font, fg="#333333", bg="#F2F2F2").pack()
        # Add
        frm_add_schedule = Frame(frm_dr_schedule, bg="#F2F2F2")
        frm_add_schedule.pack()
        # Start
        Label(frm_add_schedule, text="Start: ", font=self.body_font, fg="#333333", bg="#F2F2F2").grid(row=0, column=0)
        self.pickdate_dr_start = StringVar()
        self.entry_drdate_start = Entry(frm_add_schedule, width=10, textvariable=self.pickdate_dr_start, font=self.body_font)
        self.entry_drdate_start.bind("<Button-1>", lambda x: self.pop_calendar(self.pickdate_dr_start))
        self.entry_drdate_start.grid(row=0, column=1)
        self.pickdate_dr_start.set(datetime.today().strftime("%Y-%m-%d"))
        # pick time
        self.combo_dr_hour_start = Combobox(frm_add_schedule, values=[i for i in range(25)], width=3, font=self.body_font)
        self.combo_dr_hour_start.grid(row=0, column=2)
        self.combo_dr_hour_start.current(datetime.today().hour)
        Label(frm_add_schedule, text=":", font=self.body_font, fg="#333333", bg="#F2F2F2").grid(row=0, column=3)
        self.combo_dr_min_start = Combobox(frm_add_schedule, values=[i for i in range(60)], width=3, font=self.body_font)
        self.combo_dr_min_start.grid(row=0, column=4)
        self.combo_dr_min_start.current(datetime.today().minute)
        # End
        Label(frm_add_schedule, text="End: ", font=self.body_font, fg="#333333", bg="#F2F2F2").grid(row=1, column=0)
        self.pickdate_dr_end = StringVar()
        self.entry_drdate_end = Entry(frm_add_schedule, width=10, textvariable=self.pickdate_dr_end, font=self.body_font)
        self.entry_drdate_end.bind("<Button-1>", lambda x: self.pop_calendar(self.pickdate_dr_end))
        self.entry_drdate_end.grid(row=1, column=1)
        self.pickdate_dr_end.set(datetime.today().strftime("%Y-%m-%d"))
        # pick time
        self.combo_dr_hour_end = Combobox(frm_add_schedule, values=[i for i in range(25)], width=3, font=self.body_font)
        self.combo_dr_hour_end.grid(row=1, column=2)
        self.combo_dr_hour_end.current(datetime.today().hour)
        Label(frm_add_schedule, text=":", font=self.body_font, fg="#333333", bg="#F2F2F2").grid(row=1, column=3)
        self.combo_dr_min_end = Combobox(frm_add_schedule, values=[i for i in range(60)], width=3, font=self.body_font)
        self.combo_dr_min_end.grid(row=1, column=4)
        self.combo_dr_min_end.current(datetime.today().minute)
        # Add DR Schedule
        Button(frm_dr_schedule, text="Add", command=self.add_dr_schedule).pack()
        # All
        Label(frm_dr_schedule, text="DR Schedules", font=self.subhead_font, fg="#333333", bg="#F2F2F2").pack()
        frm_all_schedule = Frame(frm_dr_schedule, bg="#F2F2F2")
        frm_all_schedule.pack()
        # List DR Schedule
        scrollbar = Scrollbar(frm_all_schedule)
        scrollbar.pack(side='right', fill='y')
        self.lb_dr_schedule = Listbox(frm_all_schedule, width=30, height=5, font=self.list_font, yscrollcommand=scrollbar.set)
        self.lb_dr_schedule.pack(side='left', fill='both', expand=True)
        scrollbar.config(command=self.lb_dr_schedule.yview)


    def add_dr_schedule(self):
        start_time = f"{self.pickdate_dr_start.get()} {self.combo_dr_hour_start.get()}:{self.combo_dr_min_start.get()}:0"
        end_time = f"{self.pickdate_dr_end.get()} {self.combo_dr_hour_end.get()}:{self.combo_dr_min_end.get()}:0"
        # DR Start Event
        scheduler.add_job(
            func=self.exec_dr,
            trigger="date",
            run_date=datetime.strptime(start_time, "%Y-%m-%d %H:%M:%S"),
            args=["start", self.combo_dr_bright_front.get(), self.combo_dr_bright_back.get(), self.combo_dr_aircon_front.get(), self.combo_dr_aircon_back.get()],
            id=str(uuid.uuid4()),
        )
        # DR End Event
        scheduler.add_job(
            func=self.exec_dr,
            trigger="date",
            run_date=datetime.strptime(end_time, "%Y-%m-%d %H:%M:%S"),
            args=["stop"],
            id=str(uuid.uuid4()),
        )
        # Refresh DR Schedule List
        self.get_dr_schedules()

    def get_dr_schedules(self):
        self.lb_dr_schedule.delete(0, 'end')
        for item in scheduler.get_jobs():
            if item.args[0] == "start" or item.args[0] == "stop":
                self.lb_dr_schedule.insert('end', f"{item.next_run_time.strftime('%Y-%m-%d %H:%M')}  DR: {item.args[0]}")

    def update_setting(self, light_front, light_back, aircon_front, aircon_back):
        self.hue_light_front = f"{light_front} %"
        self.hue_light_back = f"{light_back} %"
        self.aircon_temperature_front = aircon_front
        self.aircon_temperature_back = aircon_back

    def exec_dr(self, action, combo_dr_bright_front=None, combo_dr_bright_back=None, combo_dr_aircon_front=None, combo_dr_aircon_back=None):
        if action == "start":
            self.dr_live_timer = 0
            self.dr_live_state = True
            # store settings
            self.normal_setting = {
                "light_front": self.hue_light_front[:-2],
                "light_back": self.hue_light_back[:-2],
                "aircon_front": self.aircon_temperature_front,
                "aircon_back": self.aircon_temperature_back,
            }
            # set dr actions
            if self.hue_light_front != "off":
                dr_light_front = int(self.hue_light_front[:-2]) - int(combo_dr_bright_front)
            else:
                dr_light_front = "off"
            if self.hue_light_back != "off":
                dr_light_back = int(self.hue_light_back[:-2]) - int(combo_dr_bright_back)
            else:
                dr_light_back = "off"
            self.set_light([dr_light_front, dr_light_back])
            if self.aircon_temperature_front != "off":
                dr_aircon_front = f"{int(self.aircon_temperature_front[:2]) + int(combo_dr_aircon_front)}c"
            else:
                dr_aircon_front = "keep"
            if self.aircon_temperature_back != "off":
                dr_aircon_back = f"{int(self.aircon_temperature_back[:2]) + int(combo_dr_aircon_back)}c"
            else:
                dr_aircon_back = "keep"
            self.aircon(dr_aircon_front, dr_aircon_back)
            self.update_setting(dr_light_front, dr_light_back, dr_aircon_front, dr_aircon_back)

        elif action == "stop":
            self.dr_live_state = False
            # recover settings
            self.update_setting(self.normal_setting["light_front"], self.normal_setting["light_back"], self.normal_setting["aircon_front"], self.normal_setting["aircon_back"])
            self.set_light([int(self.normal_setting["light_front"]), int(self.normal_setting["light_back"])])
            self.aircon(self.normal_setting["aircon_front"], self.normal_setting["aircon_back"])


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
                    if people_count != 0 and not self.dr_live_state:
                        self.set_light([100, 100])
                    # Reset Counter
                    counter_motion = 0
                    self.nobody_counter = 0

                # No people come in for 5 minutes: turn light to 50%
                elif self.nobody_counter == 300:
                    if self.rekognition() == 0:
                        self.set_light([30, 50])
                    else:
                        self.nobody_counter = 0

                # No people come in for 20 minutes: turn off light and aircon
                elif self.nobody_counter >= 600:
                    if self.rekognition() == 0:
                        if self.aircon_temperature_front != "off" or self.aircon_temperature_back != "off":
                            self.aircon("off", "off")
                        self.aircon_temperature_front = "off"
                        self.aircon_temperature_back = "off"
                        if self.hue_light_front != "off" or self.hue_light_back != "off":
                            self.set_light([0, 0])
                    else:
                        self.nobody_counter = 0

                # update sensor
                self.indoor_luminance = self.read_light()
                self.label_luminance.config(
                    text=f"Luminance:\t{format(self.indoor_luminance, '.1f')} lux"
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
                    text=f"Humidity:\t\t{format(self.indoor_humidity, '.1f')} %"
                )
                self.label_temperature.config(
                    text=f"Temperature:\t{format(self.indoor_temperature, '.1f')} °C"
                )
                self.label_di.config(
                    text=f"Comfort level:\t{self.indoor_di_cond}"
                )
                self.label_hue_light.config(text=f"Light Bar:\t  Front: {format(self.hue_light_front, '5s')} Back: {self.hue_light_back}")
                self.label_aircon.config(
                    text=f"Aircon:\t  Front: {format(self.aircon_temperature_front, '5s')} Back: {self.aircon_temperature_back}"
                )
                # update datas
                if self.dr_live_state:
                    self.dr_live_timer += 1
                    self.lbl_dr_timer.config(text=str(timedelta(seconds=self.dr_live_timer)))
                    self.btn_dr_start.config(state="disable")
                    self.btn_dr_stop.config(state="normal")
                    # set Label color
                    self.label_aircon.config(fg="#006600")
                    self.label_hue_light.config(fg="#006600")
                    # info status
                    self.lbl_info_status.config(text="status: DR", fg="#006600")
                else:
                    self.btn_dr_start.config(state="normal")
                    self.btn_dr_stop.config(state="disable")
                    # info status
                    self.label_aircon.config(fg="#333333")
                    self.label_hue_light.config(fg="#333333")
                    # info status
                    self.lbl_info_status.config(text="status: normal", fg="#333333", font=self.body_font)
                    # DR countdown
                    schedules = [{"time": item.next_run_time, "arg0": item.args[0]} for item in scheduler.get_jobs()]
                    for schedule in schedules:
                        if schedule["arg0"] == "start":
                            time_diff = schedule["time"].replace(tzinfo=None) - datetime.now().replace(tzinfo=None)
                            if time_diff <= timedelta(seconds=6):
                                self.lbl_info_status.config(text=f"status: DR after {int(time_diff.total_seconds())} s", fg="#006600", font=self.body_font)

                if self.nobody_counter == 0:
                    motion_status = "Motion Detected!"
                else:
                    motion_status = str(timedelta(seconds=self.nobody_counter))
                self.label_nobody_counter.config(text=f"Nobody Timer:\t{motion_status}")
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
                REKOGNITION_URL, headers=HEADER
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
            self.aircon("25c", "26c")
            self.aircon_temperature_front = "25c"
            self.aircon_temperature_back = "26c"
        elif people_now > 2 and self.rek_people == 1:
            self.aircon("24c", "26c")
            self.aircon_temperature_front = "24c"
            self.aircon_temperature_back = "26c"
        elif people_now == 1 and self.rek_people > 1:
            self.aircon("25c", "26c")
            self.aircon_temperature_front = "25c"
            self.aircon_temperature_back = "26c"

    def aircon(self, front_command, back_command):
        # Aircon API
        try:
            message = requests.post(
                AIRCON_URL,
                headers={
                    "Authorization": f"Bearer {TOKEN}",
                    "Content-Type": "application/json",
                },
                data=json.dumps({"action_front": front_command, "action_back": back_command}),
            ).json()
            logger.info(f"[Aircon]\nset to: {command}\n")
            if message["status"] == "success":
                self.aircon_temperature_front = front_command
                self.aircon_temperature_back = back_command
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
        self.indoor_di = self.indoor_temperature - 0.55 * (
            1 - 0.01 * self.indoor_humidity
        ) * (self.indoor_temperature - 14.5)

    def generate_condition(self):
        if self.indoor_di <= 21:
            self.indoor_di_cond = "Comfortable"
        elif 21 < self.indoor_di <= 24:
            self.indoor_di_cond = "Slightly Warm"
        elif 24 < self.indoor_di <= 27:
            self.indoor_di_cond = "Warm"
        elif 27 < self.indoor_di <= 29:
            self.indoor_di_cond = "Hot"
        elif self.indoor_di > 29:
            self.indoor_di_cond = "Very Hot"

    def get_schedule(self):
        response = requests.get(SCHEDULE_URL, headers=HEADER).json()
        self.list_schedule = response
        self.lb_schedule.delete(0, 'end')
        for item in self.list_schedule:
            self.lb_schedule.insert('end', f"{item['time'][:-3]}  {format(item['device'], '<15s')}{item['command']}")

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

    def set_light(self, *brightness_settings):
        for index, brightness in enumerate(*brightness_settings):
            device_num = index + 1
            if brightness == 0:
                self.bridge.set_light(device_num, "on", False)
                if device_num == 1:
                    self.hue_light_front = "off"
                elif device_num == 2:
                    self.hue_light_back = "off"
            else:
                self.bridge.set_light(device_num, "on", True)
                self.bridge.set_light(device_num, "hue", 41442)
                self.bridge.set_light(device_num, "sat", 0)
                self.bridge.set_light(device_num, "bri", int(brightness * 255 / 100))
                if device_num == 1:
                    self.hue_light_front = f"{brightness} %"
                elif device_num == 2:
                    self.hue_light_back = f"{brightness} %"
            logger.info(f"[Hue Light Bar] set {device_num} to {brightness}")


def main():
    # Assign pins
    pir = int(os.environ.get("PIR_PIN", "8"))
    # Set GPIO to pin numbering
    GPIO.setmode(GPIO.BOARD)
    # Setup GPIO pin PIR as input
    GPIO.setup(pir, GPIO.IN)
    logger.info(f"PIR Sensor initializing on pin {pir}")
    # Start up sensor
    # time.sleep(2)
    logger.info("Active")
    logger.info("Press Ctrl+c to end program")
    MotionDetect(pir)


if __name__ == "__main__":
    main()
