@echo off
chcp 65001 >nul
setlocal
set "BASE=%~dp0"
set "PYTHONPATH=%BASE%vendor;%PYTHONPATH%"
start "" "C:\Program Files\Python311\pythonw.exe" "%BASE%run.py"
