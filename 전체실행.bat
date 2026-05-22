@echo off
chcp 65001 > nul
echo.
echo ========================================
echo   전체 실행  (자르기 → 페이지 생성)
echo ========================================
echo.

echo [1/2] 데이터 자르기...
python slice_data.py
if %errorlevel% neq 0 (
    echo.
    echo [오류] slice_data.py 실패. 중단합니다.
    pause
    exit /b 1
)

echo.
echo [2/2] 페이지 생성...
set /p COUNT=<build_count.txt
python build.py %COUNT%
if %errorlevel% neq 0 (
    echo.
    echo [오류] build.py 실패. 중단합니다.
    pause
    exit /b 1
)

echo.
echo ========================================
echo   완료!  총 %COUNT%개 페이지 생성됨
echo ========================================
echo.
pause
