import random
import sys
from collections import OrderedDict

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger

from common import python_box
from desktop_pet import RelaxPet


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
                if type(task.get("cron")) == int:
                    scheduler.add_job(func=self.show_path, kwargs={"config": task},
                                      trigger=IntervalTrigger(seconds=task.get("cron")), max_instances=10)
                else:
                    scheduler.add_job(func=self.show_path, kwargs={"config": task},
                                      trigger=CronTrigger.from_crontab(task.get("cron")), max_instances=10)
        scheduler.start()
        return scheduler


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
    DesktopTip().start_schedule(config, True)
