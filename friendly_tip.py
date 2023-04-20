import random
import sys
import time

from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.cron import CronTrigger

from common import python_box
from desktop_pet import RelaxPet


def show_path(path: str, delay: int = 50, width: int = 150, transparency: float = 0.3):
    try:
        pet.move(random.randint(0, 1080), random.randint(0, 1920))
        pet.show_path(path, delay, width, transparency)
    except Exception as e:
        print(e)


if __name__ == '__main__':
    config = python_box.read_config("config/config_desktop_tip.ini", {
        "showPath": "path/to/png",
        "delay": 50,
        "width": 150,
        "transparency": 0.3,
        "cron": "*/10 * * * *",
    })
    if not config:
        print("请配置并重新运行")
        sys.exit(0)
    pet = RelaxPet()
    scheduler = BlockingScheduler()
    scheduler.add_job(func=show_path, args=[config.get("showPath"), config.get("delay"), config.get("width"),
                                            config.get("transparency")],
                      trigger=CronTrigger.from_crontab(config.get("cron")))
    scheduler.start()
