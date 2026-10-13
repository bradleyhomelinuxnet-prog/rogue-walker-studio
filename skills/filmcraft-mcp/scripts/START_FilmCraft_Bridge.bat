@echo off
title FilmCraft (bridge mode - control port 9876)
REM Edit the next line to the folder that holds filmcraft.exe
set "FC_DIR=C:\PATH\TO\filmcraft"
echo Launching FilmCraft with the control channel on 127.0.0.1:9876 ...
echo Leave this window open while Claude is driving the app.
cd /d "%FC_DIR%"
start "" "filmcraft.exe" --control 9876
echo FilmCraft started. You can minimize this window.
pause
