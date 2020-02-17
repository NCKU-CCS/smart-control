import glob
from tkinter import *
from PIL import Image, ImageTk


NCKU_IMG = '/home/pi/smart-control/smart_room/scripts/img/NCKU.png'

tk_root = Tk()

frm_image = Frame(tk_root)
frm_image.pack(side='left')

# img = ImageTk.PhotoImage(Image.open(path).resize((100, 100)))
ncku_img = ImageTk.PhotoImage(Image.open(NCKU_IMG).resize((100, 100)))
Label(frm_image, image=ncku_img, width=100, height=100).pack()

tk_root.mainloop()