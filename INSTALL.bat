@ECHO OFF
TITLE %~N0

ECHO Install Python
python-3.9.0-amd64-webinstall.exe /quiet InstallAllUsers=0 Include_launcher=1 PrependPath=1

ECHO Update system path variable
SETLOCAL ENABLEEXTENSIONS
set ORGINAL_PATH=%PATH%
FOR /F "TOKENS=2*" %%A IN ('REG QUERY "HKLM\SYSTEM\CurrentControlSet\Control\Session Manager\Environment" /v Path ^|FIND /I "Path"') DO (
    SET PATH=%%B
)
SET PATH=%ORGINAL_PATH%;%PATH%

ECHO Get additional libraries
py -3.9 -m pip install pyglet
py -3.9 -m pip install numpy

ECHO Please verify that everything installed correctly
PAUSE
