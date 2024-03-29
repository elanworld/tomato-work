import os
import subprocess
import sys
import time
import webbrowser

from common import gui, python_box


class Sheep:
    def __init__(self):
        self.sheep_list = []  # type: list[subprocess.Popen]

    def find_sheep_exec(self):
        if not python_box.is_admin():
            exe = r"C:\Program Files\WindowsApps\6469Adriano.esheep_2.6.64.0_x64__ddd79p2qwj4yr\DesktopPet\eSheep.exe"
            if os.path.exists(exe):
                return exe
        else:
            app_dir = r"C:\Program Files\WindowsApps"
            last_path = r"DesktopPet\eSheep.exe"
            dir_list = python_box.dir_list(app_dir, return_dir=True, filter_str=".*esheep.*")
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
            last.terminate()
        else:
            print("all sheep killed")

    def remove_all(self):
        for sheep in self.sheep_list:
            sheep.kill()
        self.sheep_list.clear()


if __name__ == '__main__':
    sheep = Sheep()
    try:
        sheep.add()
        sheep.add()
        time.sleep(3)
        sheep.remove_all()
    except PermissionError as e:
        print(f"权限异常，可尝试卸载esheep重新安装\n{e.__str__()}")
    except Exception as e:
        print(e.__str__())
