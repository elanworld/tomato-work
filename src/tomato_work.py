import os
import random
import subprocess
import sys
import time
import webbrowser
from ctypes import Structure, windll, c_uint, sizeof, byref

import pyautogui
import win32con
import win32gui
import ctypes

from common import gui, python_box
from common import python_box as box
from common.mqtt_utils import MqttBase
from tools.server_box.homeassistant_mq_entity import HomeAssistantEntity


class Sheep:
    def __init__(self):
        self.sheep_list = []  # type: list[subprocess.Popen]

    def find_sheep_exec(self):
        if not box.is_admin():
            exe = r"C:\Program Files\WindowsApps\6469Adriano.esheep_2.6.64.0_x64__ddd79p2qwj4yr\DesktopPet\eSheep.exe"
            if os.path.exists(exe):
                return exe
        else:
            app_dir = r"C:\Program Files\WindowsApps"
            last_path = r"DesktopPet\eSheep.exe"
            dir_list = box.dir_list(app_dir, return_dir=True, filter_str=".*esheep.*")
            if len(dir_list) > 1:
                for i in range(len(dir_list) - 1, -1, -1):
                    if "neutral" in dir_list[i]:
                        dir_list.remove(dir_list[i])
            if len(dir_list) > 0:
                exe_path = os.path.join(app_dir, dir_list[0], last_path)
                if os.path.exists(exe_path):
                    return exe_path
        askyesno = gui.message().askyesno("番茄钟", "是否从应用商店下载体验更好的版本?")
        if askyesno:
            webbrowser.open("https://www.microsoft.com/store/apps/9MX2V0TQT6RM", new=0, autoraise=True)
        for path in sys.path:
            join = os.path.join(path, "bin", "DesktopPet.exe")
            if os.path.exists(join):
                return join

    def add(self):
        sheep_exe = self.find_sheep_exec()
        if sheep_exe is None:
            return
        process = subprocess.Popen([sheep_exe, ],
                                   stdout=subprocess.PIPE,
                                   stderr=subprocess.STDOUT,
                                   stdin=subprocess.DEVNULL)
        self.sheep_list.append(process)
        return process

    def remove(self):
        if len(self.sheep_list) > 0:
            last = self.sheep_list[len(self.sheep_list) - 1]
            self.sheep_list.remove(last)
            last.kill()
        else:
            print("all sheep killed")

    def remove_all(self):
        for sheep in self.sheep_list:
            sheep.kill()
        self.sheep_list.clear()


class LASTINPUTINFO(Structure):
    _fields_ = [
        ('cbSize', c_uint),
        ('dwTime', c_uint),
    ]


def get_idle_duration():
    lastInputInfo = LASTINPUTINFO()
    lastInputInfo.cbSize = sizeof(lastInputInfo)
    windll.user32.GetLastInputInfo(byref(lastInputInfo))
    millis = windll.kernel32.GetTickCount() - lastInputInfo.dwTime
    return int(millis / 1000.0)


def show_msg(text, timeout=None):
    os.system(f'mshta vbscript:CreateObject("Wscript.Shell").popup("{text}",{timeout},"番茄钟",64)(window.close)')


def question_window(title, start_relax_time):
    randint = random.randint(20, 100)
    randint1 = random.randint(20, 100)
    question = f"开始休息时间已过{int((time.time() - start_relax_time) / 60)}分钟!"
    input_str = pyautogui.prompt(title=title, text=question, timeout=1000 * 15,
                                 default=f"放松几分钟！不休息请回答算术题!{randint}+{randint1}")
    if input_str == str(randint + randint1):
        return True


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


def get_start_time():
    # getting the library in which GetTickCount64() resides
    lib = ctypes.windll.kernel32
    # calling the function and storing the return value
    t = lib.GetTickCount64()
    # since the time is in milliseconds i.e. 1000 * seconds
    # therefore truncating the value
    t = int(str(t)[:-3])
    return t


class PomodoroClock:
    host = "mq host"
    port = "mq port"
    message = "send message"
    ini = "config/config_tomato.ini"
    today = "today"
    use_time = "use time"

    def __init__(self, config: dict, **kwargs):
        self._today = config.get(self.today)
        self._use_time = float(config.get(self.use_time))
        self.ha = None
        if config.get(self.message):
            base = MqttBase(config.get(self.host), int(config.get(self.port)))
            base.connect()
            self.ha = HomeAssistantEntity(base)
            self.ha.config_topic("day_use", "当日使用时长")

    def __del__(self):
        if self.ha:
            self.ha.mq.close()

    def run(self):
        if "test" in sys.argv:
            is_cal = False  # 是否计算跳过
            work_time = 2  # 工作时间
            relax_need_time = 5  # 要求休息时间
            ide_need_time = 4  # 检测空闲时间
            wait_loop_time = 2 # 等待循环空闲时间
        else:
            is_cal = False
            work_time = 25 * 60
            relax_need_time = 5 * 60
            ide_need_time = 4 * 60
            wait_loop_time = 60
        title = "番茄钟"
        text = "番茄钟开始"
        balloon_tip = None
        try:
            balloon_tip = WindowsBalloonTip(title, text)
        except Exception as e:
            print(e)
        pyautogui.confirm(title=title, text=text, timeout=3 * 5000)
        # 空闲等待三十分钟
        wait_time = 0
        for _ in range(30):
            if get_idle_duration() < wait_loop_time:
                pyautogui.confirm(title=title, text=text)
                break
            time.sleep(wait_loop_time)
            wait_time += wait_loop_time
        pyautogui.confirm(title=title, text=text, timeout=5 * 5000)
        # 番茄钟开始
        time.sleep(work_time)
        self.add_send_time(work_time)
        pyautogui.confirm(title=title, text="开始休息", timeout=5 * 1000)
        start_relax_time = time.time()  # 开始休息时间点
        sheep = Sheep()
        sheep.add()
        count = 0
        while True:
            count += 1
            time.sleep(relax_need_time)
            if get_idle_duration() > ide_need_time:
                break
            self.add_send_time(relax_need_time)
            # 没超时三次提醒一次
            if count % 3 == 0:
                if is_cal:
                    if question_window(title, start_relax_time):
                        break
                sheep.add()
        sheep.remove_all()
        if balloon_tip:
            balloon_tip.destroy()

    def add_send_time(self, duration: float):
        """
        写入时间信息并发送ha服务器
        :param duration: 增加时间，秒
        :return:
        """
        # 新的一天重计时
        if self._today != python_box.date_format(day=True):
            self._today = python_box.date_format(day=True)
            self._use_time = 0
            config[self.today] = self._today
        self._use_time += duration / 60
        config[self.use_time] = self._use_time
        python_box.write_config(config, PomodoroClock.ini)
        if self.ha:
            self.ha.send_state(f"{'%.2f' % (self._use_time)} 分钟")


if __name__ == '__main__':
    config = python_box.read_config(PomodoroClock.ini,
                                    {("%s" % PomodoroClock.host): "localhost",
                                     ("%s" % PomodoroClock.port): "1883",
                                     ("%s" % PomodoroClock.message): "0#是否发送消息1 0", PomodoroClock.today: 0,
                                     PomodoroClock.use_time: 0, }, )
    if not config:
        print("请配置并重新运行")
        sys.exit(0)
    clock = PomodoroClock(config)
    if get_start_time() < 200:
        time.sleep(300)
    if "task" in sys.argv:
        clock.run()
    else:
        for _ in range(24):
            clock.run()
    if clock.ha:
        clock.ha.mq.close()
