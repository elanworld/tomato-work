# python tomato_work.py
import sys
import time
import types
from collections import OrderedDict

import paho.mqtt.client as mqtt
import pyautogui
from infi.systray import SysTrayIcon

from common import python_box
from desktop_esheep import Sheep
from desktop_pet import RelaxPet
from tools.server_box.homeassistant_mq_entity import HomeAssistantEntity
from tools.server_box.mqtt_utils import MqttBase
from tools.tomato_work.friendly_tip import DesktopTip
from win_util import get_idle_duration, get_start_time, move_window_to_second_screen


class Timer:
    def __init__(self):
        self.exit_tag = None
        self.start = time.time()

    def init(self):
        self.start = time.time()

    def get_duration(self):
        return time.time() - self.start

    def sleep_ide(self, sec: float, need_ide: float = None, init=False, loop_do: types.FunctionType = None,
                  loop_do_time: int = None):
        start = time.time()
        if init:
            self.start = start
        for i in range(int(sec)):
            idle_duration = get_idle_duration()
            if need_ide and need_ide <= idle_duration:
                return int(time.time() - start)
            if self.exit_tag is True:
                return True
            if loop_do and loop_do_time and (i + 1 % loop_do_time) == 0:
                loop_do(i + 1)
            time.sleep(1)
        return int(time.time() - start)


class PomodoroClock:
    host = "mq host"
    port = "mq port"
    message = "send message"
    ini = "config/config_tomato.ini"
    today = "today"
    use_time = "use time"
    over_time = "over time"
    name = "tomato"
    title = "番茄钟"
    tomato_time = "tomato time"
    tomato_relax_time = "tomato relax time"
    run_loop = "run loop"
    move_window_time = "move windows tip loop time"
    cmd_start_tomato = "cmd start tomato"
    cmd_end_tomato = "cmd end tomato"
    cmd_finish_tomato = "cmd finish tomato"

    def __init__(self, config: dict, **kwargs):
        self.config = config
        self.pet = RelaxPet()
        self._today = self.config.get(self.today)
        self._exit_tag = None
        self.state = ""
        self.send_state = self.config.get(self.message) == 1
        self.sheep = Sheep()
        self.timer = Timer()
        self._use_time = float(config.get(self.use_time))
        self._over_time = float(config.get(self.over_time))
        self.desktop_tip = DesktopTip()
        self.config_tomato_desktop_tip_end = None  # type: OrderedDict
        self.config_tomato_desktop_tip_start = None  # type: OrderedDict
        self.schedule_start = None
        self.schedule_end = None
        if self.send_state:
            try:
                def will_set(client: mqtt.Client):
                    tmp = HomeAssistantEntity(None, self.name)
                    client.will_set(tmp.status_topic, "offline")

                base = MqttBase(self.config.get(self.host), int(self.config.get(self.port)), None, will_set)
                self.entity_use = HomeAssistantEntity(base, self.name)
                self.entity_over = HomeAssistantEntity(base, self.name)
                self.entity_tip = HomeAssistantEntity(base, self.name)
                self.entity_tomato = HomeAssistantEntity(base, self.name)
                self.entity_tomato_run = HomeAssistantEntity(base, self.name)
                self.entity_use.send_sensor_config_topic("day_use", "番茄使用时长", unit="分钟", expire_after=None, keep=True)
                self.entity_over.send_sensor_config_topic("over_time", "番茄超时时间", unit="分钟", expire_after=None,
                                                          keep=True)
                self.entity_tip.send_switch_config_topic("tip", "番茄休息提醒", None)
                self.entity_tomato.send_switch_config_topic("tomato", "番茄计时状态", None)
                self.entity_tomato_run.send_switch_config_topic("tomato_run", "番茄运行", None)
            except Exception as e:
                self.log_msg(e)

    def __del__(self):
        if self.send_state:
            self.entity_use.mq.close()
        self.sheep.remove_all()

    def show_state(self, *args):
        pyautogui.confirm(title=self.state, text=f"{int(self.timer.get_duration() / 60)}分钟")

    def screen_tip(self):
        try:
            self.pet.state(1)
            self.pet.move(10, 1000, 1800, 10, 1)
            self.pet.state(0)
        except Exception as e:
            self.log_msg(e)

    def action_start(self):
        if self.send_state:
            self.entity_tomato.send_switch_state(True)
            self.entity_tomato_run.send_switch_state(True)
        self.state = "番茄钟计时开始"
        self.log_msg(self.state)
        # 自定义命令
        if config.get(self.cmd_start_tomato):
            self.log_msg(python_box.command(config.get(self.cmd_start_tomato)))
        # 桌面提示
        if self.config_tomato_desktop_tip_start and self.config_tomato_desktop_tip_start.get("enable") == 1:
            self.schedule_start = self.desktop_tip.start_schedule(self.config_tomato_desktop_tip_start, None)
        self.timer.init()

    def action_end(self):
        if self.send_state:
            self.entity_tomato.send_switch_state(False)
        self.state = "番茄钟计时结束"
        self.log_msg(self.state)
        self.timer.init()
        if config.get(self.cmd_end_tomato):
            self.log_msg(python_box.command(config.get(self.cmd_end_tomato)))
        if self.schedule_start:
            self.schedule_start.shutdown()
        if self.config_tomato_desktop_tip_end and self.config_tomato_desktop_tip_end.get("enable") == 1:
            self.schedule_end = self.desktop_tip.start_schedule(self.config_tomato_desktop_tip_end, None)

    def action_finish(self):
        if self.send_state:
            self.entity_tomato_run.send_switch_state(False)
        self.sheep.remove_all()
        if config.get(self.cmd_finish_tomato):
            self.log_msg(python_box.command(config.get(self.cmd_finish_tomato)))
        if self.schedule_end:
            self.schedule_end.shutdown()
        self.log_msg("番茄钟休息完毕")

    def run(self):
        work_time = float(config.get(PomodoroClock.tomato_time)) * 60
        relax_need_time = float(config.get(PomodoroClock.tomato_relax_time)) * 60
        try:
            self.pet.run()
            self.pet.state(0)
        except Exception as e:
            self.log_msg(e)
        text = "番茄钟开始"
        if get_idle_duration() > 5:
            pyautogui.confirm(title=self.title, text=text, timeout=1 * 1000)
        # 空闲时等待五小时
        wait_time = 0
        while True:
            if get_idle_duration() < 2:
                pyautogui.confirm(title=self.title, text=text)
                break
            time.sleep(2)
            wait_time += 2
            if wait_time > 60 * 60 * 5:
                self.log_msg("超时退出")
                return
        self.action_start()
        # 开始番茄
        if self.timer.sleep_ide(work_time) is True:
            return
        self.action_end()
        self.add_use_time(work_time)
        pyautogui.confirm(title=self.title, text="开始休息", timeout=3 * 1000)
        self.add_sheep(self.sheep)
        # 休息并提醒
        count = 0
        while True:
            count += 1
            self.send_tip()
            try:
                for _ in range(5):
                    res = self.timer.sleep_ide(relax_need_time / 5, relax_need_time,
                                               loop_do=self.move_windows,
                                               loop_do_time=self.config.get(PomodoroClock.move_window_time))
                    if res is True or res < relax_need_time / 5:
                        raise BrokenPipeError("break")  # 空闲满足跳出多层循环
                    self.screen_tip()
                    self.add_over_use_time(res)
            except BrokenPipeError:
                break
            # 每超时三次提醒一次
            if count % 3 == 0:
                self.add_sheep(self.sheep)
        self.action_finish()

    @staticmethod
    def move_windows(sec: int = None):
        if get_idle_duration() < 15 and sec and sec > 15:
            move_window_to_second_screen()

    @staticmethod
    def add_sheep(sheep: Sheep):
        try:
            sheep.add()
        except PermissionError as e:
            pyautogui.confirm(title="异常", text=f"权限异常，可尝试卸载esheep重新安装\n{e.__str__()}", timeout=10 * 1000)
        except Exception as e:
            pyautogui.confirm(title=f"{type(e)}异常", text=e.__str__(), timeout=10 * 1000)

    def add_use_time(self, duration: float):
        """
        写入时间信息并发送ha服务器
        :param duration: 增加时间，秒
        :return:
        """
        self.new_day_build()
        self._use_time += duration
        self.config[self.use_time] = self._use_time
        self.save_state()

    def add_over_use_time(self, duration: float):
        self.new_day_build()
        self._over_time += + duration
        self._use_time += duration
        self.config[self.over_time] = self._over_time
        self.config[self.use_time] = self._use_time
        self.save_state()

    def new_day_build(self):
        # 新的一天重计时
        if self._today != python_box.date_format(day=True):
            self._today = python_box.date_format(day=True)
            self._use_time = 0
            self._over_time = 0
            self.config[self.today] = self._today
            self.config[self.over_time] = self._over_time

    def save_state(self):
        python_box.write_config(self.config, PomodoroClock.ini)
        if self.send_state:
            try:
                self.entity_use.send_sensor_state(f"{'%.2f' % (self._use_time / 60)}")
                self.entity_over.send_sensor_state(f"{'%.2f' % (self._over_time / 60)}")
            except Exception as e:
                self.log_msg(e)

    def send_tip(self):
        if self.send_state:
            self.entity_tip.send_switch_state(True)
            time.sleep(.2)
            self.entity_tip.send_switch_state(False)

    def log_msg(self, msg):
        python_box.log(msg, file="config/log_tomato.log")


if __name__ == '__main__':
    try:
        config = python_box.read_config(PomodoroClock.ini,
                                        {("%s" % PomodoroClock.tomato_time): 25,
                                         ("%s" % PomodoroClock.tomato_relax_time): 5,
                                         ("%s" % PomodoroClock.run_loop): 1,
                                         ("%s" % PomodoroClock.move_window_time): None,
                                         ("%s" % PomodoroClock.host): "localhost",
                                         ("%s" % PomodoroClock.port): "1883",
                                         ("%s" % PomodoroClock.message): "0#是否发送消息1 0",
                                         ("%s" % PomodoroClock.cmd_start_tomato): "None#开始执行命令",
                                         ("%s" % PomodoroClock.cmd_end_tomato): "None#结束执行命令",
                                         ("%s" % PomodoroClock.cmd_finish_tomato): "None#程序结束执行命令",
                                         PomodoroClock.today: 0,
                                         PomodoroClock.use_time: 0, PomodoroClock.over_time: 0, }, )
        default_dict = {"enable": "0", "task1": {
            "showPath": "path/to/png",
            "delay": 50,
            "width": 150,
            "transparency": 0.3,
            "cron": "*/10 * * * *",

        }}
        config_tomato_desktop_tip_start = python_box.read_config("config/config_tomato_desktop_tip_start.ini",
                                                                 default_dict)
        config_tomato_desktop_tip_end = python_box.read_config("config/config_tomato_desktop_tip_end.ini",
                                                               default_dict)
        if not config:
            print("请配置并重新运行")
            sys.exit(0)
        clock = PomodoroClock(config)
        clock.config_tomato_desktop_tip_start = config_tomato_desktop_tip_start
        clock.config_tomato_desktop_tip_end = config_tomato_desktop_tip_end


        def exit_process(clock):
            clock.timer.exit_tag = True


        menu = (("显示状态", None, clock.show_state),)
        systray = SysTrayIcon(None, "tomato sheep clock", menu,
                              on_quit=lambda x: exit_process(clock))
        systray.start()
        if get_start_time() < 200:
            time.sleep(300)
        for _ in range(config.get(PomodoroClock.run_loop)):
            clock.run()
        systray.shutdown()
        clock.__del__()
    except Exception as e:
        pyautogui.confirm(title="运行错误", text=e.__str__())
        systray.shutdown()
