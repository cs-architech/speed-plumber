@echo off
chcp 65001 > nul
echo.
echo ========================================
echo   데이터 자르기 실행
echo ========================================
echo.
python slice_data.py
if %errorlevel% neq 0 (
    echo.
    echo [오류] slice_data.py 실행에 실패했습니다.
    pause
    exit /b 1
)
echo.
pause
