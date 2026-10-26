@echo off
title Hematoscan API Server
cd /d D:\hematoscan
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0start-server.ps1"
pause
