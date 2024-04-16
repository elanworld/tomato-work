import time
import pyautogui
import win32_util


def confirm(title="", text="", **kwargs):
    start = time.time()
    while win32_util.is_window_fullscreen():
        if time.time() - start > 3600:
            break
        time.sleep(1)
    return pyautogui.confirm(title=title, text=text, **kwargs)

def alert(title="", text="", **kwargs):
    start = time.time()
    while win32_util.is_window_fullscreen():
        if time.time() - start > 3600:
            break
        time.sleep(1)
    return pyautogui.alert(title=title, text=text, **kwargs)
