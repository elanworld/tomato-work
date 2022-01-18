pyinstaller -Fw --add-binary "..\bin\DesktopPet.exe;bin" -p ..\..\.. tomato_work.py
copy dist\tomato_work.exe ..\main.exe