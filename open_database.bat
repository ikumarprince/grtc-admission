@echo off
title Open Database in SQLite Browser
cd /d "%~dp0"
echo Opening admissions.db in DB Browser for SQLite...

set DB_PATH=%~dp0data\admissions.db

where sqlitebrowser >nul 2>nul
if %errorlevel% equ 0 (
    start "" sqlitebrowser "%DB_PATH%"
    exit
)

if exist "C:\Program Files\DB Browser for SQLite\DB Browser for SQLite.exe" (
    start "" "C:\Program Files\DB Browser for SQLite\DB Browser for SQLite.exe" "%DB_PATH%"
    exit
)

if exist "C:\Program Files (x86)\DB Browser for SQLite\DB Browser for SQLite.exe" (
    start "" "C:\Program Files (x86)\DB Browser for SQLite\DB Browser for SQLite.exe" "%DB_PATH%"
    exit
)

echo Opening with default SQLite viewer...
start "" "%DB_PATH%"
