# generate from base common code
import tkinter as tk
import tkinter.messagebox
from tkinter import filedialog
from tkinter import simpledialog
from tkinter.ttk import Progressbar
def message():
    global root
    root = _top()
    return tkinter.messagebox
def _top():
    global root
    win = root if root else tkinter.Tk()
    win.withdraw()
    return win