#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
indexnow_submit.py — IndexNow 프로토콜로 네이버·Bing에 URL 일괄 통지
(IndexNow는 Bing/네이버/Yandex/Seznam이 공동 채택한 프로토콜이라
 api.indexnow.org 한 번 호출로 참여 엔진 전체에 전달된다)

사전 준비:
  1. INDEXNOW_KEY 값과 동일한 내용의 "{key}.txt" 파일이
     https://reviewkorea.co.kr/plumber2/{key}.txt 로 접근 가능해야 함
     (webmaster_files/{key}.txt 에 넣으면 netlify_deploy.py가 자동 배포)
  2. 의존 패키지: pip install requests
"""

import json
import sys
from datetime import date
from pathlib import Path
from urllib.request import urlopen
from xml.etree import ElementTree as ET

try:
    import requests
except ImportError:
    print("[ERROR] 의존성 미설치. 아래 명령어 실행 후 재시도:")
    print("        pip install requests")
    sys.exit(1)

# ─── 설정 ─────────────────────────────────────────────────────────────────────
BASE_DIR       = Path(__file__).parent
STATE_FILE     = BASE_DIR / "indexnow_state.json"
SITE_DOMAIN    = "https://reviewkorea.co.kr/plumber2"
HOST           = "reviewkorea.co.kr"
SITEMAP_URL    = f"{SITE_DOMAIN}/sitemap.xml"
INDEXNOW_KEY   = "d8710c8a90b77bef8ddad14029aa9bed"
KEY_LOCATION   = f"{SITE_DOMAIN}/{INDEXNOW_KEY}.txt"
INDEXNOW_ENDPOINT = "https://api.indexnow.org/indexnow"

BATCH_SIZE = 10000  # IndexNow 1회 요청 최대 URL 수


# ─── 상태 관리 ────────────────────────────────────────────────────────────────
def load_state() -> dict:
    if STATE_FILE.exists():
        try:
            return json.loads(STATE_FILE.read_text(encoding="utf-8"))
        except Exception:
            pass
    return {"submitted": [], "daily": {}}


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

    sub_sitemaps = tree.findall(".//sm:sitemap/sm:loc", ns)
    if sub_sitemaps:
        urls = []
        for loc in sub_sitemaps:
            urls.extend(fetch_urls(loc.text.strip()))
        return urls

    return [loc.text.strip() for loc in tree.findall(".//sm:url/sm:loc", ns)]


# ─── IndexNow 제출 ────────────────────────────────────────────────────────────
def submit_batch(urls: list[str]) -> bool:
    try:
        resp = requests.post(
            INDEXNOW_ENDPOINT,
            headers={"Content-Type": "application/json; charset=utf-8"},
            json={
                "host": HOST,
                "key": INDEXNOW_KEY,
                "keyLocation": KEY_LOCATION,
                "urlList": urls,
            },
            timeout=30,
        )
    except Exception as e:
        print(f"  [FAIL] 요청 오류: {e}")
        return False

    # IndexNow는 200/202 성공, 상세 오류코드는 https://www.indexnow.org/documentation 참고
    if resp.status_code in (200, 202):
        print(f"  [OK] {len(urls)}개 제출 성공 (status={resp.status_code})")
        return True

    print(f"  [FAIL] status={resp.status_code} body={resp.text[:300]}")
    return False


# ─── 메인 ─────────────────────────────────────────────────────────────────────
def main() -> int:
    print("=" * 60)
    print("  indexnow_submit.py — 네이버/Bing IndexNow 제출")
    print("=" * 60)

    force = "--force" in sys.argv

    state = load_state()
    submitted = set(state.setdefault("submitted", []))
    daily = state.setdefault("daily", {})

    print("[1/3] 사이트맵 파싱 중...")
    all_urls = fetch_urls(SITEMAP_URL)
    if not all_urls:
        print("[ERROR] URL 목록을 가져올 수 없습니다.")
        return 1
    print(f"      전체 URL: {len(all_urls)}개")

    targets = all_urls if force else [u for u in all_urls if u not in submitted]
    if not targets:
        print("[SKIP] 신규/미제출 URL 없음 — 제출할 것이 없습니다.")
        return 0

    print(f"[2/3] 제출 대상: {len(targets)}개 {'(전체 강제 재제출)' if force else '(신규분만)'}")

    print("[3/3] IndexNow 제출 중...")
    today = str(date.today())
    ok_total = 0
    for i in range(0, len(targets), BATCH_SIZE):
        batch = targets[i : i + BATCH_SIZE]
        if submit_batch(batch):
            submitted.update(batch)
            ok_total += len(batch)

    state["submitted"] = sorted(submitted)
    daily[today] = daily.get(today, 0) + ok_total
    save_state(state)

    print("=" * 60)
    print(f"  완료: {ok_total}/{len(targets)}개 제출 성공")
    print(f"  누적 제출: {len(submitted)}/{len(all_urls)}개")
    print("=" * 60)
    return 0 if ok_total == len(targets) else 1


if __name__ == "__main__":
    sys.exit(main())
