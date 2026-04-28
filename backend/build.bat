@echo off
cls

echo ===================================================
echo      SDN Guard HPC Engine  -  Build System v2.0
echo ===================================================

cd /d %~dp0

echo.
echo [INFO] Working directory: %CD%

echo.
echo [1/3] Cleaning old build...
if exist engine.exe del engine.exe

echo.
echo [2/3] Compiling C++ backend...

g++ -O3 -std=c++17 -fopenmp ^
    main.cpp ^
    DetectionEngine.cpp ^
    TrafficGenerator.cpp ^
    -o engine.exe

if %errorlevel% neq 0 (
    echo.
    echo ===================================================
    echo   BUILD FAILED
    echo ===================================================
    echo.
    echo Common causes:
    echo   - OpenMP not supported  ^(try: g++ --version^)
    echo   - Missing .cpp files in this folder
    echo   - Syntax error in source files
    echo.
    pause
    exit /b %errorlevel%
)

echo.
echo [3/3] Build successful.

echo.
echo Running quick validation test...
echo.
engine.exe --nodes 10 --packets 5000 --target 1,2 --attack ICMP_FLOOD

echo.
echo ===================================================
echo   engine.exe is ready  -  run main.py to launch UI
echo ===================================================
pause
