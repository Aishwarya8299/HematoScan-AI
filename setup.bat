@echo off
title Hematoscan Setup
cd /d D:\hematoscan
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0setup.ps1"
