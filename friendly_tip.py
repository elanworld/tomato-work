import logging
import multiprocessing
import random
import sys
import threading
import time
from collections import OrderedDict
from datetime import datetime, timezone

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.base import BaseTrigger
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger

from common import python_box
from desktop_pet import RelaxPet


class Scheduler:
    def __init__(self):
        self.timers = []

    def add_job(self, func, trigger=None, args=(), kwargs={}):
        def job_wrapper():
            while job_wrapper.running:
                func(*args, **kwargs)
                if trigger:
                    time.sleep(trigger)
                else:
                    break

        job_wrapper.running = True
        timer_thread = threading.Thread(target=job_wrapper)
        timer_thread.start()
        self.timers.append(timer_thread)

    def shutdown(self):
        for timer_thread in self.timers:
            timer_thread._target.running = False #设置方法标志


class DesktopTip:

    def __init__(self):
        self.pet = RelaxPet()

    def show_path(self, path: str = None, delay: int = 50, width: int = 150, transparency: float = 0.3, config=None):
        try:
            self.pet.move(random.randint(0, 1080), random.randint(0, 1920))
            if config:
                self.pet.show_path(config=config)
            else:
                self.pet.show_path(path, delay, width, transparency)
        except Exception as e:
            python_box.log(e)

    def start_schedule(self, config, block=None):
        scheduler = BlockingScheduler() if block else BackgroundScheduler()
        for task in config.values():
            if type(task) == OrderedDict:
                crontab = IntervalTrigger(seconds=task.get("cron")) if type(
                    task.get("cron")) == int else CronTrigger.from_crontab(task.get("cron"))
                scheduler.add_job(self.execute_with_timeout, args=(
                    self.show_path, (), {"config": task}, self.get_interval_from_cron(basetrigger=crontab)),
                                  trigger=crontab, max_instances=10)
        scheduler.start()
        return scheduler

    def start_schedule_interval(self, config, *args, **kwargs):
        scheduler = Scheduler()
        for task in config.values():
            if type(task) == OrderedDict:
                interval = task.get("cron")
                if type(interval) == int:
                    scheduler.add_job(self.show_path, kwargs={"config": task}, trigger=interval)
                else:
                    logging.warning(f"cron {interval} not int type, skip task")
        return scheduler

    def execute_with_timeout(self, target_func, args=(), kwargs=None, timeout=10):
        # 创建子进程
        if kwargs is None:
            kwargs = {}
        process = multiprocessing.Process(target=target_func, args=args, kwargs=kwargs)

        # 启动子进程
        process.start()

        # 定时器回调函数
        def kill_process():
            if process.is_alive():
                python_box.log("Task timeout. Terminating process...")
                process.terminate()  # 终止子进程
                process.join()  # 等待子进程结束

        # 设置定时器，在 timeout 秒后执行 kill_process
        timer = threading.Timer(timeout, kill_process)
        timer.start()

        # 等待子进程结束
        process.join()

        # 取消定时器
        timer.cancel()

    def get_interval_from_cron(self, basetrigger: BaseTrigger):
        # 获取当前时间
        now = datetime.now(timezone.utc)

        next_fire_time = basetrigger.get_next_fire_time(now, now)
        # 计算间隔时间
        interval_seconds = (next_fire_time - now).total_seconds()

        return interval_seconds


if __name__ == '__main__':
    config = python_box.read_config("config/config_desktop_tip.ini", {"task1": {
        "showPath": "path/to/png",
        "delay": 50,
        "width": 150,
        "transparency": 0.3,
        "cron": "*/10 * * * *",
    }})
    if not config:
        python_box.log("请配置并重新运行")
        sys.exit(0)
    python_box.log("start")
    DesktopTip().start_schedule(config, True)
