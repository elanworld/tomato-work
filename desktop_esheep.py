import os
import subprocess
import sys
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
        try:
            sheep_exe = self.find_sheep_exec()
            if sheep_exe is None:
                return
            process = subprocess.Popen([sheep_exe, ],
                                       stdout=subprocess.PIPE,
                                       stderr=subprocess.STDOUT,
                                       stdin=subprocess.DEVNULL)
            self.sheep_list.append(process)
        except Exception as e:
            print("打开esheep失败")
            raise Exception(f"打开eshep失败,{e.__str__()}")
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
