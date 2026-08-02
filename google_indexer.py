#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
google_indexer.py — Google 인덱싱 API 순차 제출
1시간마다 10개씩, 하루 최대 100개
1라운드: 전체 URL 1회 제출 → 2라운드: 전체 URL 1회 더 제출 → 완료 후 영구 종료
"""

import json
import sys
import time
from datetime import date, datetime
from pathlib import Path
from urllib.request import urlopen
from xml.etree import ElementTree as ET

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
STATE_FILE           = BASE_DIR / "indexer_state.json"
SITE_DOMAIN          = "https://reviewkorea.co.kr/plumber2"
SITEMAP_URL          = f"{SITE_DOMAIN}/sitemap.xml"
INDEXING_API_SCOPE   = "https://www.googleapis.com/auth/indexing"
INDEXING_ENDPOINT    = "https://indexing.googleapis.com/v3/urlNotifications:publish"

BATCH_SIZE  = 10   # 1회 실행 시 제출 개수
DAILY_LIMIT = 100  # 하루 최대 제출 개수


# ─── 상태 관리 ────────────────────────────────────────────────────────────────
def load_state() -> dict:
    if STATE_FILE.exists():
        try:
            return json.loads(STATE_FILE.read_text(encoding="utf-8"))
        except Exception:
            pass
    return {
        "round1": {},   # URL → 제출 시각 (1라운드)
        "round2": {},   # URL → 제출 시각 (2라운드)
        "daily":  {},
        "completed": False,
    }


def save_state(state: dict):
    STATE_FILE.write_text(
        json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8"
    )


# ─── 사이트맵 파싱 ────────────────────────────────────────────────────────────
def fetch_urls(sitemap_url: str) -> list[str]:
    ns = {"sm": "http://www.sitemaps.org/schemas/sitemap/0.9"}
    try:
        with urlopen(sitemap_url, timeout=30) as r:
            tree = ET.parse(r)
    except Exception as e:
        print(f"[WARN] 사이트맵 접근 실패 ({sitemap_url}): {e}")
        return []

    # 사이트맵 인덱스 → 하위 사이트맵 재귀 파싱
    sub_sitemaps = tree.findall(".//sm:sitemap/sm:loc", ns)
    if sub_sitemaps:
        urls = []
        for loc in sub_sitemaps:
            urls.extend(fetch_urls(loc.text.strip()))
        return urls

    return [loc.text.strip() for loc in tree.findall(".//sm:url/sm:loc", ns)]


# ─── Google 인증 ─────────────────────────────────────────────────────────────
def get_access_token() -> str:
    credentials = service_account.Credentials.from_service_account_file(
        str(SERVICE_ACCOUNT_FILE),
        scopes=[INDEXING_API_SCOPE],
    )
    credentials.refresh(AuthRequest())
    return credentials.token


# ─── URL 제출 ─────────────────────────────────────────────────────────────────
def notify_url(token: str, url: str) -> bool:
    try:
        resp = requests.post(
            INDEXING_ENDPOINT,
            headers={
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json",
            },
            json={"url": url, "type": "URL_UPDATED"},
            timeout=30,
        )
        data = resp.json()
    except Exception as e:
        print(f"  [FAIL] {url} — 요청 오류: {e}")
        return False

    if "error" in data:
        print(f"  [FAIL] {url} — {data['error'].get('message', data)}")
        return False

    print(f"  [OK]  {url}")
    return True


# ─── 메인 ─────────────────────────────────────────────────────────────────────
def main() -> int:
    print("=" * 60)
    print("  google_indexer.py  —  Google 인덱싱 순차 제출")
    print("=" * 60)

    state     = load_state()
    round1    = state.setdefault("round1", {})
    round2    = state.setdefault("round2", {})
    daily     = state.setdefault("daily", {})

    # 2라운드까지 완료 → 영구 종료
    if state.get("completed"):
        print("[DONE] 1·2라운드 제출 모두 완료 — 더 이상 실행하지 않습니다.")
        return 0

    today = str(date.today())
    today_count = daily.get(today, 0)
    if today_count >= DAILY_LIMIT:
        print(f"[SKIP] 오늘 이미 {today_count}개 제출 완료 (일일 한도 {DAILY_LIMIT}개)")
        return 0

    remaining  = DAILY_LIMIT - today_count
    batch_size = min(BATCH_SIZE, remaining)

    if not SERVICE_ACCOUNT_FILE.exists():
        print(f"[ERROR] {SERVICE_ACCOUNT_FILE} 없음")
        return 1

    # 전체 URL 수집
    print(f"[1/3] 사이트맵 파싱 중... ({SITEMAP_URL})")
    all_urls = fetch_urls(SITEMAP_URL)
    if not all_urls:
        print("[ERROR] URL 목록을 가져올 수 없습니다.")
        return 1
    total = len(all_urls)
    print(f"      전체 URL: {total}개")

    # 배치 선정
    # 우선순위: 1라운드 미제출 → 2라운드 미제출 (1라운드 완료 후) → 없으면 종료 처리
    r1_pending = sorted([u for u in all_urls if u not in round1])
    r2_pending = sorted([u for u in all_urls if u in round1 and u not in round2])

    r1_done = len(round1)
    r2_done = len(round2)

    # 현재 라운드 표시
    if r1_pending:
        current_round = 1
        candidates = r1_pending
        print(f"      [1라운드] 진행중 {r1_done}/{total}")
    elif r2_pending:
        current_round = 2
        candidates = r2_pending
        print(f"      [2라운드] 진행중 {r2_done}/{total}  (1라운드 완료)")
    else:
        # 둘 다 완료
        state["completed"] = True
        save_state(state)
        print(f"[DONE] 1·2라운드 {total}개씩 제출 모두 완료 — 워크플로우를 종료합니다.")
        return 0

    batch = candidates[:batch_size]

    print(f"[2/3] 인증 중...")
    try:
        token = get_access_token()
    except Exception as e:
        print(f"[ERROR] 인증 실패: {e}")
        return 1
    print("      인증 성공")

    print(f"[3/3] URL 제출 중... ({len(batch)}개 | 오늘 누계 {today_count} → {today_count + len(batch)}개)")
    now_str = datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
    success = 0
    for url in batch:
        if notify_url(token, url):
            if current_round == 1:
                round1[url] = now_str
            else:
                round2[url] = now_str
            success += 1
        time.sleep(1)

    daily[today] = today_count + success

    # 이번 배치로 2라운드 완료됐는지 재확인
    if current_round == 2 and len(round2) >= total:
        state["completed"] = True
        print(f"\n[DONE] 2라운드 마지막 배치 완료 — 전체 {total}개 × 2회 제출 종료!")

    save_state(state)

    print("=" * 60)
    print(f"  완료: {success}/{len(batch)}개 제출 성공")
    print(f"  오늘 누계: {daily[today]}개 / {DAILY_LIMIT}개")
    if current_round == 1:
        print(f"  1라운드: {len(round1)}/{total}개")
    else:
        print(f"  2라운드: {len(round2)}/{total}개")
    print("=" * 60)
    return 0


if __name__ == "__main__":
    sys.exit(main())
