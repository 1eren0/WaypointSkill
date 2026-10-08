@echo off
rem Waypoint guncelleyici. Kullanici cift tiklar; yapay zeka bu dosyayi kendisi calistirmaz.
cd /d "%~dp0.." && powershell -NoProfile -Command "irm https://raw.githubusercontent.com/erenuzman/WaypointSkill/main/install.ps1 | iex" & echo. & echo Bitti. Bu pencereyi kapatip yapay zekaya "guncelledim" yaz. & pause & exit /b
