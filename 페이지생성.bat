@echo off
chcp 65001 > nul
echo.
echo ========================================
echo   페이지 생성 실행
echo ========================================
echo.
if exist build_count.txt (
    set /p COUNT=<build_count.txt
    echo [알림] %COUNT%개 페이지를 생성합니다.
    echo.
    python build.py %COUNT%
) else (
    echo [알림] build_count.txt 없음 — 먼저 데이터자르기.bat를 실행하세요.
    echo [기본] 단일 페이지 1개를 생성합니다.
    echo.
    python build.py
)
if %errorlevel% neq 0 (
    echo.
    echo [오류] build.py 실행에 실패했습니다.
    pause
    exit /b 1
)
echo.
pause
