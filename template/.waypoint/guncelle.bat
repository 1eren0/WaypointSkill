@echo off
rem Waypoint guncelleyici. Kullanici cift tiklar; yapay zeka bu dosyayi kendisi calistirmaz.
cd /d "%~dp0.." && powershell -NoProfile -Command "gh api repos/erenuzman/WaypointSkill/contents/install.ps1 -H 'Accept: application/vnd.github.raw' | Out-String | iex" & echo. & echo Bitti. Bu pencereyi kapatip yapay zekaya "guncelledim" yaz. & pause & exit /b
