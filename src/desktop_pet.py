import subprocess
import time

import requests


class RelaxPet:
    def __init__(self):
        self.app_path = r"D:\program\data\app\desktop-box\desktop-box.exe"
        self.app_api = "http://localhost:8090/"

    def run(self):
        self.process = subprocess.Popen([self.app_path, ],
                                        stdout=subprocess.PIPE,
                                        stderr=subprocess.STDOUT,
                                        stdin=subprocess.DEVNULL)

    def __del__(self):
        self.close()

    def move(self, x, y, x1=None, y1=None, duration=None):
        body = {"x": x, "y": y, "x1": x1, "y1": y1, "duration": duration}
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

    def close(self):
        self.process.kill()


if __name__ == '__main__':
    pet = RelaxPet()
    pet.run()
    time.sleep(1)
    pet.move(10, 1000, 1800, 10, 1)
    pet.state(0.5)
    time.sleep(1)
