import time
import pyautogui
import win32_util


def confirm(wait_time=3600, **kwargs):
    start = time.time()
    while win32_util.is_window_fullscreen():
        if time.time() - start > wait_time:
            break
        time.sleep(1)
    return pyautogui.confirm(**kwargs) != 'Cancel'

def alert(wait_time=3600, **kwargs):
    start = time.time()
    while win32_util.is_window_fullscreen():
        if time.time() - start > wait_time:
            break
        time.sleep(1)
    return pyautogui.alert(**kwargs)
