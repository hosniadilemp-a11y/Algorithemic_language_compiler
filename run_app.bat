@echo off
echo ========================================
echo    AlgoCompiler Web Server
echo ========================================
echo.
echo Clearing parser cache...
del /Q src\compiler\parser.out 2>nul
del /Q src\compiler\parsetab.py 2>nul
echo.
echo Starting AlgoCompiler web server...
echo Server will be available at: http://localhost:5000
echo Press Ctrl+C to stop the server
echo.
python src\web\app.py
pause
