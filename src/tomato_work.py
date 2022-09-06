import sys
import time

import pyautogui
from infi.systray import SysTrayIcon

from common import python_box
from desktop_esheep import Sheep
from desktop_pet import RelaxPet
from tools.server_box.homeassistant_mq_entity import HomeAssistantEntity
from tools.server_box.mqtt_utils import MqttBase
from win_util import WindowsBalloonTip, get_idle_duration, question_window, get_start_time


class Timer:
    def __init__(self):
        self.exit_tag = None
        self.start = time.time()

    def init(self):
        self.start = time.time()

    def get_duration(self):
        return time.time() - self.start

    def sleep_ide(self, sec: float, need_ide: float = None, init=False):
        start = time.time()
        if init:
            self.start = start
        for i in range(int(sec)):
            if need_ide and need_ide <= get_idle_duration():
                return int(time.time() - start)
            if self.exit_tag is True:
                return True
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

    def __init__(self, config: dict, **kwargs):
        self.pet = RelaxPet()
        self._today = config.get(self.today)
        self._exit_tag = None
        self.use_entity = None
        self.over_entity = None
        self.state = ""
        self.sheep = Sheep()
        self.timer = Timer()
        self._use_time = float(config.get(self.use_time))
        self._over_time = float(config.get(self.over_time))
        if config.get(self.message):
            try:
                pass
                base = MqttBase(config.get(self.host), int(config.get(self.port)))
                self.use_entity = HomeAssistantEntity(base)
                self.use_entity.send_sensor_config_topic("day_use", "当日使用时长", unit="分钟", keep=True)
                self.over_entity = HomeAssistantEntity(base)
                self.over_entity.send_sensor_config_topic("over_time", "超时时间", unit="分钟", keep=True)
            except Exception as e:
                self.log_msg(e)

    def __del__(self):
        if self.use_entity:
            self.use_entity.mq.close()
        self.sheep.remove_all()
        self.timer.exit_tag = True
        self.pet.__del__()

    def show_state(self, *args):
        pyautogui.confirm(title=self.state, text=f"{int(self.timer.get_duration() / 60)}分钟")

    def run(self):
        if "test" in sys.argv:
            is_cal = False  # 是否计算跳过
            work_time = 2.0  # 工作时间
            relax_need_time = 5.0  # 要求休息时间
        else:
            is_cal = False
            work_time = 25 * 60
            relax_need_time = 5 * 60
        title = "番茄钟"
        text = "番茄钟开始"
        try:
            self.pet.run()
            self.pet.state(0)
        except Exception as e:
            self.log_msg(e)
        if get_idle_duration() > 5:
            pyautogui.confirm(title=title, text=text, timeout=1 * 1000)
        # 空闲等待五小时
        wait_time = 0
        while True:
            if get_idle_duration() < 2:
                pyautogui.confirm(title=title, text=text)
                break
            time.sleep(2)
            wait_time += 2
            if wait_time > 60 * 60 * 5:
                return
        self.log_msg("番茄钟计时开始")
        self.state = "计时开始"
        self.timer.init()
        if self.timer.sleep_ide(work_time) is True:
            return
        self.log_msg("番茄钟计时结束，开始休息")
        self.state = "休息开始"
        self.timer.init()
        self.add_use_time(work_time)
        pyautogui.confirm(title=title, text="开始休息", timeout=3 * 1000)
        start_relax_time = time.time()  # 开始休息时间点
        self.sheep.add()
        count = 0
        while True:
            count += 1
            ide = 0
            for _ in range(5):
                res = self.timer.sleep_ide(relax_need_time / 5, relax_need_time)
                ide = True if res is True else ide + res
                try:
                    if res >= relax_need_time / 5:
                        self.pet.state(1)
                        self.pet.move(10, 1000, 1800, 10, 1)
                        self.pet.state(0)
                except Exception as e:
                    self.log_msg(e)
                if ide is True:
                    return
            if ide < relax_need_time:
                break
            self.add_use_time(ide)
            # 每超时三次提醒一次
            if count % 3 == 0:
                if is_cal:
                    if question_window(title, start_relax_time):
                        break
                self.sheep.add()
                self.add_overtime(ide * 3)
        self.sheep.remove_all()
        self.log_msg("番茄钟休息完毕")

    def add_use_time(self, duration: float):
        """
        写入时间信息并发送ha服务器
        :param duration: 增加时间，秒
        :return:
        """
        self.new_day_build()
        self._use_time += duration
        config[self.use_time] = self._use_time
        self.save_state()

    def add_overtime(self, duration: float):
        self.new_day_build()
        self._over_time = self._over_time + duration
        config[self.over_time] = self._over_time
        self.save_state()

    def new_day_build(self):
        # 新的一天重计时
        if self._today != python_box.date_format(day=True):
            self._today = python_box.date_format(day=True)
            self._use_time = 0
            self._over_time = 0
            config[self.today] = self._today
            config[self.over_time] = self._over_time

    def save_state(self):
        python_box.write_config(config, PomodoroClock.ini)
        if self.use_entity:
            try:
                self.use_entity.send_state(f"{'%.2f' % (self._use_time / 60)}")
            except Exception as e:
                self.log_msg(e)
        if self.over_entity:
            try:
                self.over_entity.send_state(f"{'%.2f' % (self._over_time / 60)}")
            except Exception as e:
                self.log_msg(e)

    def log_msg(self, msg):
        python_box.log(msg, file="config/log_tomato.log")


if __name__ == '__main__':
    config = python_box.read_config(PomodoroClock.ini,
                                    {("%s" % PomodoroClock.host): "localhost",
                                     ("%s" % PomodoroClock.port): "1883",
                                     ("%s" % PomodoroClock.message): "0#是否发送消息1 0", PomodoroClock.today: 0,
                                     PomodoroClock.use_time: 0, PomodoroClock.over_time: 0, }, )
    if not config:
        print("请配置并重新运行")
        sys.exit(0)
    clock = PomodoroClock(config)


    def exit_process(clock):
        clock.__del__()


    menu = (("显示状态", None, clock.show_state),)
    systray = SysTrayIcon(None, "tomato sheep clock", menu,
                          on_quit=lambda x: exit_process(clock))
    systray.start()
    if get_start_time() < 200:
        time.sleep(300)
    if "task" in sys.argv:
        clock.run()
    else:
        for _ in range(24):
            clock.run()
    clock.__del__()
    systray.shutdown()
