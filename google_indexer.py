#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
google_indexer.py — Google 인덱싱 API 강제 수집 요청
하루 1회: 메인 홈 URL(/) + 사이트맵 URL(/sitemap.xml) 2개만 요청

사전 준비:
  1. Google Cloud Console에서 Indexing API 활성화
  2. 서비스 계정 생성 → JSON 키 다운로드 → service_account.json 으로 저장
  3. Google Search Console에서 해당 서비스 계정 이메일을 소유자로 등록

실행 방법:
  pip install google-auth requests
  python google_indexer.py
"""

import json
import sys
from datetime import date, datetime
from pathlib import Path

try:
    import requests
    from google.oauth2 import service_account
    from google.auth.transport.requests import Request as AuthRequest
except ImportError:
    print("[ERROR] 의존성 미설치. 아래 명령어 실행 후 재시도:")
    print("        pip install google-auth requests")
    sys.exit(1)

# ─── 설정 ─────────────────────────────────────────────────────────────────────
BASE_DIR             = Path(__file__).parent
SERVICE_ACCOUNT_FILE = BASE_DIR / "service_account.json"
LOG_FILE             = BASE_DIR / "indexer_log.json"
SITE_DOMAIN          = "https://speed-plumber.netlify.app"
INDEXING_API_SCOPE   = "https://www.googleapis.com/auth/indexing"
INDEXING_ENDPOINT    = "https://indexing.googleapis.com/v3/urlNotifications:publish"

# 하루 1회만 요청하는 2개 핵심 URL
TARGET_URLS = [
    f"{SITE_DOMAIN}/",
    f"{SITE_DOMAIN}/sitemap.xml",
]


# ─── 중복 실행 방지 (하루 1회) ────────────────────────────────────────────────
def already_ran_today() -> bool:
    if not LOG_FILE.exists():
        return False
    try:
        log = json.loads(LOG_FILE.read_text(encoding="utf-8"))
        return log.get("last_run_date") == str(date.today())
    except Exception:
        return False


def save_run_log(results: list[dict]):
    log = {
        "last_run_date": str(date.today()),
        "last_run_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "results": results,
    }
    LOG_FILE.write_text(json.dumps(log, ensure_ascii=False, indent=2), encoding="utf-8")


# ─── 인증 ─────────────────────────────────────────────────────────────────────
def get_access_token() -> str:
    credentials = service_account.Credentials.from_service_account_file(
        str(SERVICE_ACCOUNT_FILE),
        scopes=[INDEXING_API_SCOPE],
    )
    credentials.refresh(AuthRequest())
    return credentials.token


# ─── URL 수집 요청 ────────────────────────────────────────────────────────────
def notify_url(token: str, url: str) -> dict:
    resp = requests.post(
        INDEXING_ENDPOINT,
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        },
        json={"url": url, "type": "URL_UPDATED"},
        timeout=30,
    )
    try:
        return resp.json()
    except Exception:
        return {"status_code": resp.status_code, "text": resp.text}


# ─── 메인 ─────────────────────────────────────────────────────────────────────
def main() -> int:
    print("=" * 52)
    print("  google_indexer.py  —  Google 수집 요청")
    print("=" * 52)

    if not SERVICE_ACCOUNT_FILE.exists():
        print(f"[ERROR] {SERVICE_ACCOUNT_FILE} 없음")
        print("  → Google Cloud Console에서 서비스 계정 JSON 키를 다운로드하세요.")
        return 1

    if already_ran_today():
        print(f"[SKIP] 오늘({date.today()}) 이미 실행됨 — 하루 1회 제한")
        return 0

    print("[1/2] 서비스 계정 인증 중...")
    try:
        token = get_access_token()
    except Exception as e:
        print(f"[ERROR] 인증 실패: {e}")
        return 1
    print("  인증 성공")

    print("[2/2] URL 수집 요청 전송...")
    results = []
    for url in TARGET_URLS:
        result = notify_url(token, url)
        status = result.get("urlNotificationMetadata", {}).get("latestUpdate", {}).get("type", "")
        if "error" in result:
            print(f"  [FAIL] {url}")
            print(f"         오류: {result['error'].get('message', result)}")
        else:
            print(f"  [OK]  {url}")
            if status:
                print(f"         상태: {status}")
        results.append({"url": url, "response": result})

    save_run_log(results)
    print("=" * 52)
    print(f"  완료: {len(TARGET_URLS)}개 URL 요청 전송")
    print(f"  로그: {LOG_FILE}")
    print("=" * 52)
    return 0


if __name__ == "__main__":
    sys.exit(main())
