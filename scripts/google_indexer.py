#!/usr/bin/env python3
"""
scripts/google_indexer.py
────────────────────────────────────────────────────────────
Google 인덱싱 API로 2개 URL만 전송: / 와 /sitemap.xml

사전 준비:
  1. Google Search Console 에서 서비스 계정 생성 후 키 파일 저장
     → 프로젝트 루트에 service_account.json 으로 저장
  2. 해당 서비스 계정 이메일을 Search Console 속성 소유자로 추가
  3. 의존 패키지: pip install oauth2client requests

실행: python scripts/google_indexer.py
      python scripts/google_indexer.py --dry-run   # URL 출력만
"""

import json
import sys
import argparse
from pathlib import Path

try:
    from oauth2client.service_account import ServiceAccountCredentials
    import requests as req
except ImportError:
    print("[ERROR] 필요 패키지가 없습니다. 아래 명령을 실행하세요:", file=sys.stderr)
    print("  pip install oauth2client requests", file=sys.stderr)
    sys.exit(1)

SITE_URL   = "https://plumbers24.netlify.app"
SCOPES     = ["https://www.googleapis.com/auth/indexing"]
KEY_FILE   = Path(__file__).resolve().parent.parent / "service_account.json"
INDEX_API  = "https://indexing.googleapis.com/v3/urlNotifications:publish"

URLS_TO_SUBMIT = [
    f"{SITE_URL}/",
    f"{SITE_URL}/sitemap.xml",
]


def get_access_token() -> str:
    if not KEY_FILE.exists():
        print(f"[ERROR] 서비스 계정 키 파일 없음: {KEY_FILE}", file=sys.stderr)
        print("  service_account.json 을 프로젝트 루트에 저장하세요.", file=sys.stderr)
        sys.exit(1)
    creds = ServiceAccountCredentials.from_json_keyfile_name(str(KEY_FILE), scopes=SCOPES)
    return creds.get_access_token().access_token


def submit_url(session: req.Session, url: str, token: str) -> dict:
    resp = session.post(
        INDEX_API,
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        },
        json={"url": url, "type": "URL_UPDATED"},
        timeout=15,
    )
    return resp.json()


def main():
    parser = argparse.ArgumentParser(description="Google 인덱싱 API URL 제출")
    parser.add_argument("--dry-run", action="store_true", help="실제 전송 없이 URL만 출력")
    args = parser.parse_args()

    print("[google_indexer] 시작")

    if args.dry_run:
        print("[dry-run] 전송 대상 URL:")
        for u in URLS_TO_SUBMIT:
            print(f"  → {u}")
        return

    token = get_access_token()

    with req.Session() as sess:
        for url in URLS_TO_SUBMIT:
            try:
                result = submit_url(sess, url, token)
                if "urlNotificationMetadata" in result:
                    print(f"  ✅ 성공: {url}")
                else:
                    print(f"  ❌ 실패: {url}")
                    print(f"     응답: {json.dumps(result, ensure_ascii=False)}")
            except Exception as e:
                print(f"  ❌ 오류: {url} — {e}", file=sys.stderr)

    print("[google_indexer] 완료")


if __name__ == "__main__":
    main()
