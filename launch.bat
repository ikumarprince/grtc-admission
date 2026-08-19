@echo off
title Candidate Admission System Launcher (HTTPS Secured)
echo ===================================================================
echo   Starting Candidate Admission System with SSL / HTTPS...
echo ===================================================================
echo.
echo   [PC Browser Link]     : https://localhost:5000
echo   [Phone/WiFi Link]     : https://192.168.1.154:5000
echo.
echo   NOTE FOR PHONE:
echo   Jab pehli baar phone me kholein aur "Your connection is not private" ya "Warning"
echo   dikhe, toh bas "Advanced" -> "Proceed / Continue to 192.168.1.154" par click karein.
echo   Iske baad mobile par CAMERA aur saare features 100% smoothly work karenge!
echo ===================================================================
echo.

cd /d "%~dp0"

start "" "https://localhost:5000"
python -m uvicorn app:app --host 0.0.0.0 --port 5000 --ssl-keyfile ssl\key.pem --ssl-certfile ssl\cert.pem --reload
pause
