import ctypes
import random
import time
from typing import List

import pyautogui
import win32api
import win32con
import win32gui



def get_idle_duration():
    class LASTINPUTINFO(ctypes.Structure):
        _fields_ = [
            ('cbSize', ctypes.c_uint),
            ('dwTime', ctypes.c_uint),
        ]

    lastInputInfo = LASTINPUTINFO()
    lastInputInfo.cbSize = ctypes.sizeof(lastInputInfo)
    ctypes.windll.user32.GetLastInputInfo(ctypes.byref(lastInputInfo))
    millis = ctypes.windll.kernel32.GetTickCount() - lastInputInfo.dwTime
    return int(millis / 1000.0)


def question_window(title, start_relax_time):
    randint = random.randint(20, 100)
    randint1 = random.randint(20, 100)
    question = f"开始休息时间已过{int((time.time() - start_relax_time) / 60)}分钟!"
    input_str = pyautogui.prompt(title=title, text=question, timeout=1000 * 15,
                                 default=f"放松几分钟！不休息请回答算术题!{randint}+{randint1}")
    if input_str == str(randint + randint1):
        return True


def get_start_time():
    # getting the library in which GetTickCount64() resides
    lib = ctypes.windll.kernel32
    # calling the function and storing the return value
    t = lib.GetTickCount64()
    # since the time is in milliseconds i.e. 1000 * seconds
    # therefore truncating the value
    t = int(str(t)[:-3])
    return t


class WindowsBalloonTip:
    def __init__(self, title, msg):
        message_map = {
            win32con.WM_DESTROY: self.OnDestroy,
        }
        # Register the Window class.
        wc = win32gui.WNDCLASS()
        hinst = wc.hInstance = win32gui.GetModuleHandle(None)
        wc.lpszClassName = "PythonTaskbar"
        wc.lpfnWndProc = message_map  # could also specify a wndproc.
        classAtom = win32gui.RegisterClass(wc)
        # Create the Window.
        style = win32con.WS_OVERLAPPED | win32con.WS_SYSMENU
        self.hwnd = win32gui.CreateWindow(classAtom, "Taskbar", style, \
                                          0, 0, win32con.CW_USEDEFAULT, win32con.CW_USEDEFAULT, \
                                          0, 0, hinst, None)
        win32gui.UpdateWindow(self.hwnd)
        icon_flags = win32con.LR_LOADFROMFILE | win32con.LR_DEFAULTSIZE
        try:
            hicon = win32gui.LoadImage(hinst, None, \
                                       win32con.IMAGE_ICON, 0, 0, icon_flags)
        except:
            hicon = win32gui.LoadIcon(0, win32con.IDI_APPLICATION)
        flags = win32gui.NIF_ICON | win32gui.NIF_MESSAGE | win32gui.NIF_TIP
        nid = (self.hwnd, 0, flags, win32con.WM_USER + 20, hicon, "tooltip")
        win32gui.Shell_NotifyIcon(win32gui.NIM_ADD, nid)
        win32gui.Shell_NotifyIcon(win32gui.NIM_MODIFY, \
                                  (self.hwnd, 0, win32gui.NIF_INFO, win32con.WM_USER + 20, \
                                   hicon, "Balloon  tooltip", msg, 200, title))

    def OnDestroy(self, hwnd, msg, wparam, lparam):
        nid = (self.hwnd, 0)
        win32gui.Shell_NotifyIcon(win32gui.NIM_DELETE, nid)
        win32gui.PostQuitMessage(0)  # Terminate the app.

    def destroy(self):
        win32gui.DestroyWindow(self.hwnd)


def get_least_similar_monitor_rect(window_rect):
    # 获取窗口位置和大小
    x, y, w, h = window_rect

    # 获取所有监视器信息
    monitors = win32api.EnumDisplayMonitors()

    # 记录最不相似的监视器
    least_similar_monitor_rect = None
    least_similar_monitor_distance = float('-inf')

    # 遍历所有监视器
    for monitor in monitors:
        monitor_info = win32api.GetMonitorInfo(monitor[0])
        monitor_rect = monitor_info['Monitor']

        # 计算监视器的左上角坐标
        monitor_x, monitor_y = monitor_rect[0], monitor_rect[1]

        # 计算窗口左上角坐标和监视器左上角坐标的距离
        distance = abs(x - monitor_x) + abs(y - monitor_y)

        # 如果距离更大，则更新最不相似的监视器
        if distance > least_similar_monitor_distance:
            least_similar_monitor_rect = monitor_rect
            least_similar_monitor_distance = distance

    return least_similar_monitor_rect


def get_window_position_rate_on_screen(rect, monitor_rect):
    # 获取窗口的位置和大小
    left, top, right, bottom = rect
    # 计算窗口在屏幕中的坐标占比
    x = (left - monitor_rect[0]) / abs(monitor_rect[2] - monitor_rect[0])
    y = (top - monitor_rect[1]) / abs(monitor_rect[3] - monitor_rect[1])
    x1 = (right - monitor_rect[0]) / abs(monitor_rect[2] - monitor_rect[0])
    y1 = (bottom - monitor_rect[1]) / abs(monitor_rect[3] - monitor_rect[1])
    return x, y, x1, y1


def get_window_rect_from_position_rate(position, monitor_rect):
    # 计算窗口在屏幕中的实际坐标
    left = int(position[0] * abs(monitor_rect[2] - monitor_rect[0]) + monitor_rect[0])
    top = int(position[1] * abs(monitor_rect[3] - monitor_rect[1]) + monitor_rect[1])
    right = int(position[2] * abs(monitor_rect[2] - monitor_rect[0]) + monitor_rect[0])
    bottom = int(position[3] * abs(monitor_rect[3] - monitor_rect[1]) + monitor_rect[1])
    return left, top, right, bottom


def move_window_to_second_screen(device_scale: List[tuple] = None):  # device_scale: 屏幕移动后缩放，依然存在问题，移动命令不准确
    # 获取当前活跃的窗口句柄
    hwnd = win32gui.GetForegroundWindow()
    # 获取当前窗口的位置和大小
    rect_now = win32gui.GetWindowRect(hwnd)
    left, top, right, bottom = rect_now
    # 获取当前监视器
    monitor_now = win32api.GetMonitorInfo(win32api.MonitorFromPoint((left, top), win32con.MONITOR_DEFAULTTONEAREST))

    # 获取目标屏幕的位置和大小
    monitor_target = get_least_similar_monitor_rect(rect_now)
    position_rate = get_window_position_rate_on_screen(rect_now, monitor_now["Monitor"])

    # 计算出新窗口在目标屏幕的位置和大小
    x, y, x1, y1 = get_window_rect_from_position_rate(position_rate, monitor_target)
    for info in device_scale if device_scale else []:
        if info[0] == monitor_now["Device"]:
            x, y, x1, y1 = int(x * info[1]), int(y * info[1]), int(x1 * info[1]), int(y1 * info[1])

    # 判断窗口是否最大化
    placement = win32gui.GetWindowPlacement(hwnd)
    if placement[1] == win32con.SW_MAXIMIZE:
        # 如果窗口最大化，就先恢复原来的大小和位置
        win32gui.ShowWindow(hwnd, win32con.SW_RESTORE)
    # 移动窗口到新的位置
    win32gui.SetWindowPos(hwnd, win32con.HWND_TOP, x, y, x1 - x, y1 - y, win32con.SWP_NOSIZE)

    if placement[1] == win32con.SW_MAXIMIZE:
        # 最大化窗口，适应目标屏幕的大小
        time.sleep(0.05)  # 有时窗口不是最大尺寸
        win32gui.ShowWindow(hwnd, win32con.SW_MAXIMIZE)


def get_screen_resolution():
    return win32api.GetSystemMetrics(0), win32api.GetSystemMetrics(1)


# 检测当前活动窗口是否全屏
def is_window_fullscreen():
    active_window = win32gui.GetForegroundWindow()
    _, _, win_width, win_height = win32gui.GetWindowRect(active_window)
    screen_width, screen_height = get_screen_resolution()

    return (win_width, win_height) == (screen_width, screen_height)


def get_physical_resolution(device_name):
    # 获取指定显示器的分辨率设置
    dm = win32api.EnumDisplaySettings(device_name, win32con.ENUM_CURRENT_SETTINGS)
    physical_width = dm.PelsWidth
    physical_height = dm.PelsHeight
    return physical_width, physical_height


def get_screen_boundaries():
    monitors = win32api.EnumDisplayMonitors(None, None)
    boundaries = []
    for monitor in monitors:
        device_name = win32api.GetMonitorInfo(monitor[0])['Device']
        physical_width, physical_height = get_physical_resolution(device_name)
        x1 = monitor[2][0]
        y1 = monitor[2][1]
        boundaries.append((x1, y1, x1 + physical_width, y1 + physical_height))
        # boundaries.append((monitor[2]))
    return boundaries


def create_polygon(monitors):
    points = []
    for mon_left, mon_top, mon_right, mon_bottom in monitors:
        points.append((mon_left, mon_top))
        points.append((mon_right, mon_top))
        points.append((mon_right, mon_bottom))
        points.append((mon_left, mon_bottom))
    return Polygon(points)


def is_center_in_screen(point, monitor):
    center_x, center_y = point
    mon_left, mon_top, mon_right, mon_bottom = monitor
    if mon_left <= center_x <= mon_right and mon_top <= center_y <= mon_bottom:
        return True
    return False


def move_right_value_in_screen(monitors, window, move):
    """预判移动后窗口依旧在屏幕内的值"""
    left, top, right, bottom = window
    move_x, move_y = move
    x_in = 0
    y_in = 0
    for monitor in monitors:
        if is_center_in_screen((left + move_x, top), monitor):
            x_in += 1  # 移动后左x 在屏幕内
        if is_center_in_screen((right + move_x, bottom), monitor):
            x_in += 1
        if is_center_in_screen((left, top + move_y), monitor):
            y_in += 1
        if is_center_in_screen((right, bottom + move_y), monitor):
            y_in += 1
    if x_in < 2:  # 移动x后在屏幕内的次数不炒股两次
        move_x = -move_x
    if y_in < 2:  #
        move_y = -move_y
    print(monitors, window, move)
    return move_x, move_y


def is_in_screen(monitors, window):
    """当前在屏幕内"""
    left, top, right, bottom = window
    left_in = False
    right_in = False
    for monitor in monitors:
        if is_center_in_screen((left, top), monitor):
            left_in = True
        if is_center_in_screen((right, bottom), monitor):
            right_in = True
    if left_in and right_in:
        return True
    return False


def move_window(step_x=10, step_y=10):
    # 获取当前活跃的窗口句柄
    hwnd = win32gui.GetForegroundWindow()
    # 获取当前窗口的位置和大小
    rect_now = win32gui.GetWindowRect(hwnd)
    left, top, right, bottom = rect_now

    # 获取所有屏幕的边界
    monitors = get_screen_boundaries()
    if is_in_screen(monitors, rect_now):
        # 移动窗口到新的位置
        win32gui.SetWindowPos(hwnd, win32con.HWND_TOP, left + step_x, top + step_y, 0, 0,
                              win32con.SWP_NOSIZE | win32con.SWP_NOZORDER)
        if is_in_screen(monitors, win32gui.GetWindowRect(hwnd)):  # 移动后还在屏幕内
            return step_x, step_y
    # 计算新的位置
    step_x, step_y = move_right_value_in_screen(monitors, rect_now, (step_x, step_y))

    # 移动窗口到新的位置
    win32gui.SetWindowPos(hwnd, win32con.HWND_TOP, left + step_x, top + step_y, 0, 0,
                          win32con.SWP_NOSIZE | win32con.SWP_NOZORDER)
    return step_x, step_y



if __name__ == '__main__':
    move_window_to_second_screen([('\\\\.\\DISPLAY3', 1.25)])