import os
import subprocess

import requests

from common import gui


class RelaxPet:
    def __init__(self):
        self.app_path = r"D:\program\data\app\desktop-box\desktop-box.application"
        self.app_api = "http://localhost:8090/"

    def run(self):
        if not os.path.exists(self.app_path):
            os.system("start https://www.xianneng.top/file/app/")
            dirname = os.path.dirname(self.app_path)
            os.makedirs(dirname, exist_ok=True)
            os.system(f"explorer {dirname}")
            gui.message().showinfo("下载安装",
                                   message=f"{self.app_path}不存在！\n请下载网页中压缩文件:desktop-box.application.zip，解压放入已打开目录中")
        self.process = subprocess.Popen(["explorer", self.app_path, ],
                                        stdout=subprocess.PIPE,
                                        stderr=subprocess.STDOUT,
                                        stdin=subprocess.DEVNULL)

    def __del__(self):
        self.close()

    def move(self, x, y, x1=None, y1=None, duration=None):
        body = {"x": x, "y": y, "x1": x1, "y1": y1}
        if duration:
            body["duration"] = duration
        if x1 is not None:
            response = requests.post(self.app_api + "swap", json=body, timeout=5)
        else:
            response = requests.post(self.app_api + "move", json=body, timeout=5)
        if not response.text.startswith("{"):
            print(response.text)

    def state(self, transparency: float = 1):
        body = {"transparency": transparency}
        response = requests.post(self.app_api + "state", json=body, timeout=5)
        if not response.text.startswith("{"):
            print(response.text)

    def show_path(self, path: str, delay: int = 50, width: int = 150, transparency: float = 0.3):
        body = {"showPath": path, "delay": delay, "width": width, "transparency": transparency}
        response = requests.post(self.app_api + "ShowPath", json=body, timeout=5)
        if not response.text.startswith("{"):
            print(response.text)

    def close(self):
        self.process.kill()


if __name__ == '__main__':
    pet = RelaxPet()
    pet.run()
    for i in range(50):
        try:
            pet.state(1)
            pet.move(10, 1000, 1800, 10, 1)
            pet.state(0)
        except Exception as e:
            print(e)
