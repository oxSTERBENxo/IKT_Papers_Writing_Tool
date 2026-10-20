@echo off
rem Starts Starry Sky for a lecture. Students on the same Wi-Fi use the address printed below.
cd /d "%~dp0"
for /f "tokens=2 delims=:" %%a in ('ipconfig ^| findstr /c:"IPv4"') do (
  for /f "tokens=* delims= " %%b in ("%%a") do echo Students: http://%%b:8000   ^(then the lecture code^)
)
echo Instructor: http://localhost:8000
.venv\Scripts\python -m uvicorn app.main:create_app --factory --host 0.0.0.0 --port 8000
