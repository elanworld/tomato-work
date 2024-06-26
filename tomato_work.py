# python tomato_work.py
import platform
import sys
import time
import traceback
from collections import OrderedDict
from typing import Callable

import paho.mqtt.client as mqtt
from infi.systray import SysTrayIcon

import win32_util
import windows_tip
from common import python_box
from desktop_esheep import Sheep
from friendly_tip import DesktopTip
from tools.server_box.mqtt.homeassistant_mq_entity import HomeAssistantEntity
from tools.server_box.mqtt.mqtt_utils import MqttBase


class Timer:
    def __init__(self):
        self.exit_tag = None
        self.start = time.time()

    def init(self):
        self.start = time.time()

    def set_exit_tag(self, value: bool):
        self.exit_tag = value

    def get_duration(self):
        return time.time() - self.start

    def sleep_ide(self, sec: float, need_ide: float = None, loop_do: Callable[[int], None] = None,
                  loop_do_time: int = None):
        start = time.time()
        for i in range(int(sec)):
            idle_duration = win32_util.get_idle_duration()
            if need_ide and need_ide <= idle_duration:
                return time.time() - start
            if self.exit_tag is True:
                return 0
            if loop_do and loop_do_time and ((i + 1) % loop_do_time) == 0:
                loop_do(i + 1)
            time.sleep(1)
        return sec


class PomodoroClock(dict):
    host = "mq host"
    port = "mq port"
    message = "send message"
    tip_wait_full_screen = "tip wait full screen"
    ini = "config/config_tomato.ini"
    data_ini = "config/data_day_over_time.ini"
    today = "today"
    use_time = "use time"
    over_time = "over time"
    device = "device"
    name = "tag"
    title = "番茄钟"
    tomato_time = "tomato time"
    tomato_relax_time = "tomato relax time"
    run_loop = "run loop"
    move_window_time_start = "move windows tip loop time start"
    move_window_time_end = "move windows tip loop time end"
    cmd_start_tomato = "cmd start tomato"
    cmd_end_tomato = "cmd end tomato"
    cmd_finish_tomato = "cmd finish tomato"

    def __init__(self, config: dict, **kwargs):
        super().__init__()
        # data
        self.today_str = ""
        self.user_time_sec = 0
        self.over_time_sec = 0

        self.config = config
        self._exit_tag = None
        self.state = ""
        self.send_state = self.config.get(self.message) == 1
        self.sheep = Sheep()
        self.timer = Timer()
        self.desktop_tip = DesktopTip()
        self.systray = SysTrayIcon(None, "tomato sheep clock", (("显示状态", None, self.show_state),),
                                   on_quit=lambda x: self.timer.set_exit_tag(True))
        self.systray.start()
        self.config_tomato_desktop_tip_end = None  # type: OrderedDict
        self.config_tomato_desktop_tip_start = None  # type: OrderedDict
        self.schedule_start = None
        self.schedule_end = None
        if self.send_state:
            def will_set(client: mqtt.Client):
                tmp = HomeAssistantEntity(None, config.get(self.name), config.get(self.device))
                client.will_set(tmp.status_topic, "offline")

            self.base_mqtt = MqttBase(self.config.get(self.host), int(self.config.get(self.port)), None, will_set,
                                      connect_now=False)
            self.entity_use = HomeAssistantEntity(self.base_mqtt, config.get(self.name), config.get(self.device))
            self.entity_over = HomeAssistantEntity(self.base_mqtt, config.get(self.name), config.get(self.device))
            self.entity_tip = HomeAssistantEntity(self.base_mqtt, config.get(self.name), config.get(self.device))

    def __del__(self):
        self.sheep.remove_all()
        if self.send_state:
            self.base_mqtt.close()
        if getattr(self, "systray", None):
            self.systray.shutdown()

    def connect_mqtt(self):
        if self.send_state:
            self.base_mqtt.connect()
            self.entity_use.send_sensor_config_topic("day_use", "番茄使用时长", unit="分钟", expire_after=None, keep=True)
            self.entity_over.send_sensor_config_topic("over_time", "番茄超时时间", unit="分钟", expire_after=None,
                                                      keep=True)
            self.entity_tip.send_switch_config_topic("tip", "番茄休息提醒", None)

    def show_state(self, *args):
        self.window_tip(title=self.state, text=f"{int(self.timer.get_duration() / 60)}分钟", confirm=True)

    def window_tip(self, title="番茄钟", text=None, timeout=None, confirm=True):
        if confirm:
            return windows_tip.confirm(title=title, text=text, timeout=timeout, wait_time=2 * 60 * 60)
        else:
            return windows_tip.alert(title=title, text=text, timeout=timeout, wait_time=2 * 60 * 60)

    def action_start(self):
        self.state = "番茄钟计时开始"
        self.log_msg(self.state)
        # 自定义命令
        if config.get(self.cmd_start_tomato):
            self.log_msg(python_box.command(config.get(self.cmd_start_tomato)))
        # 桌面提示
        if self.config_tomato_desktop_tip_start and self.config_tomato_desktop_tip_start.get("enable") == 1:
            self.schedule_start = self.desktop_tip.start_schedule_interval(self.config_tomato_desktop_tip_start, None)
        self.timer.init()

    def action_end(self):
        self.state = "番茄钟计时结束"
        self.log_msg(self.state)
        self.timer.init()
        if config.get(self.cmd_end_tomato):
            self.log_msg(python_box.command(config.get(self.cmd_end_tomato)))
        if self.schedule_start:
            self.schedule_start.shutdown()
        if self.config_tomato_desktop_tip_end and self.config_tomato_desktop_tip_end.get("enable") == 1:
            self.schedule_end = self.desktop_tip.start_schedule_interval(self.config_tomato_desktop_tip_end, None)

    def action_finish(self):
        self.sheep.remove_all()
        if config.get(self.cmd_finish_tomato):
            self.log_msg(python_box.command(config.get(self.cmd_finish_tomato)))
        if self.schedule_end:
            self.schedule_end.shutdown()
        self.log_msg("番茄钟休息完毕")

    def run(self):
        work_time = float(config.get(PomodoroClock.tomato_time)) * 60
        relax_need_time = float(config.get(PomodoroClock.tomato_relax_time)) * 60
        # 开始提示
        text = "番茄钟开始"
        if win32_util.get_idle_duration() > 5:
            confirm = self.window_tip(title=self.title, text=text, timeout=1 * 1000, confirm=True)
            if not confirm:
                return
        # 空闲时等待五小时
        wait_time = 0
        while True:
            if win32_util.get_idle_duration() < 2:
                confirm = self.window_tip(title=self.title, text=text, confirm=True)
                if not confirm:
                    return
                break
            time.sleep(2)
            wait_time += 2
            if wait_time > 60 * 60 * 5:
                self.log_msg("超时退出")
                return
        self.action_start()
        # 开始番茄
        if self.config_tomato_desktop_tip_start.get("enable") == 1 or self.config_tomato_desktop_tip_end.get(
                "enable") == 1:
            self.desktop_tip.pet.run()
            self.desktop_tip.pet.state(0)
        if not self.timer.sleep_ide(work_time, loop_do=self.move_windows,
                                    loop_do_time=self.config.get(PomodoroClock.move_window_time_start)):
            return
        self.action_end()
        self.add_use_time(work_time)
        self.window_tip(title=self.title, text="开始休息", timeout=3 * 1000, confirm=False)
        self.add_sheep(self.sheep)
        # 休息并提醒
        count = 0
        while True:
            count += 1
            self.send_tip()
            try:
                loop_time = 5
                for _ in range(loop_time):
                    res = self.timer.sleep_ide(int(relax_need_time / loop_time), relax_need_time,
                                               loop_do=self.move_windows,
                                               loop_do_time=self.config.get(PomodoroClock.move_window_time_start))
                    if not res or res < int(relax_need_time / loop_time):
                        raise BrokenPipeError("break")  # 空闲满足跳出多层循环
                    self.add_over_use_time(res)
            except BrokenPipeError:
                break
            # 每超时三次提醒一次
            if count % 3 == 0:
                self.add_sheep(self.sheep)
        self.action_finish()

    @staticmethod
    def move_windows(*args, **kwargs):
        if win32_util.get_idle_duration() < 15:
            win32_util.move_window_to_second_screen()

    def add_sheep(self, sheep: Sheep):
        try:
            sheep.add()
        except PermissionError as e:
            self.window_tip(title="异常", text=f"权限异常，可尝试卸载esheep重新安装\n{e.__str__()}", timeout=10 * 1000, confirm=True)
        except Exception as e:
            self.window_tip(title=f"{type(e)}异常", text=e.__str__(), timeout=10 * 1000, confirm=True)

    def add_use_time(self, duration: float):
        """
        写入时间信息并发送ha服务器
        :param duration: 增加时间，秒
        :return:
        """
        self.new_day_build()
        self.user_time_sec += duration
        self.config[self.use_time] = self.user_time_sec
        self.save_state()

    def add_over_use_time(self, duration: float):
        self.new_day_build()
        self.over_time_sec += + duration
        self.user_time_sec += duration
        self.save_state()

    def new_day_build(self):
        # 新的一天重计时
        if self.today_str != python_box.date_format(day=True):
            self.today_str = python_box.date_format(day=True)
            self.user_time_sec = 0
            self.over_time_sec = 0

    def save_state(self):
        python_box.json_dump(PomodoroClock.data_ini,
                             python_box.object_attr_dump(self, ["today_str", "over_time_sec", "user_time_sec"]))
        if self.send_state:
            self.entity_use.send_sensor_state(f"{'%.2f' % (self.user_time_sec / 60)}")
            self.entity_over.send_sensor_state(f"{'%.2f' % (self.over_time_sec / 60)}")

    def send_tip(self):
        if self.send_state:
            self.entity_tip.send_switch_state(True)
            time.sleep(.2)
            self.entity_tip.send_switch_state(False)

    def log_msg(self, msg):
        python_box.log(msg, file="config/log_tomato.log", console=True, flush_now=True)


if __name__ == '__main__':
    config = python_box.read_config(PomodoroClock.ini,
                                    {("%s" % PomodoroClock.tomato_time): 25,
                                     ("%s" % PomodoroClock.tomato_relax_time): 5,
                                     ("%s" % PomodoroClock.run_loop): 1,
                                     ("%s" % PomodoroClock.move_window_time_start): None,
                                     ("%s" % PomodoroClock.move_window_time_end): None,
                                     ("%s" % PomodoroClock.host): "localhost",
                                     ("%s" % PomodoroClock.port): "1883",
                                     ("%s" % PomodoroClock.message): "0#是否发送消息1 0",
                                     ("%s" % PomodoroClock.tip_wait_full_screen): "0#提示等待全体退出1 0",
                                     ("%s" % PomodoroClock.device): platform.node(),
                                     ("%s" % PomodoroClock.name): None,
                                     ("%s" % PomodoroClock.cmd_start_tomato): "None#开始执行命令",
                                     ("%s" % PomodoroClock.cmd_end_tomato): "None#结束执行命令",
                                     ("%s" % PomodoroClock.cmd_finish_tomato): "None#程序结束执行命令", }, )
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
    data_over_time = python_box.json_load(PomodoroClock.data_ini, {})
    if not config:
        print("请配置并重新运行")
        sys.exit(0)
    clock = PomodoroClock(config)
    try:
        python_box.object_attr_load(data_over_time, clock)
        clock.config_tomato_desktop_tip_start = config_tomato_desktop_tip_start
        clock.config_tomato_desktop_tip_end = config_tomato_desktop_tip_end
        clock.connect_mqtt()

        if win32_util.get_start_time() < 200:
            time.sleep(300)  # 开机等待
        for _ in range(config.get(PomodoroClock.run_loop)):
            clock.run()
        clock.__del__()
    except Exception as e:
        clock.__del__()
        traceback.print_exc()
