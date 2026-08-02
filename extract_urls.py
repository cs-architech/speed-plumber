# -*- coding: utf-8 -*-
"""
extract_urls.py
pages_bank/page-XXXX 폴더에서 HTML title을 읽어
URL 목록을 deployed_urls.txt로 저장합니다.
"""
import re
import sys
from pathlib import Path
from datetime import datetime

SITE_DOMAIN = "https://speed-plumber.netlify.app"
BANK_DIR = Path(__file__).parent / "pages_bank"
OUTPUT_FILE = Path(__file__).parent / "deployed_urls.txt"

def main():
    pages = sorted(BANK_DIR.glob("page-????"))
    total = len(pages)
    print(f"총 {total}개 페이지 발견, 처리 중...", flush=True)

    lines = []
    lines.append("=" * 70)
    lines.append(f"  speed-plumber.netlify.app 배포 URL 전체 목록")
    lines.append(f"  생성일시: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    lines.append(f"  총 페이지 수 (pages_bank 기준): {total}개")
    lines.append("=" * 70)
    lines.append("")

    count = 0
    for page_dir in pages:
        html_path = page_dir / "index.html"
        if not html_path.exists():
            continue
        with open(html_path, "rb") as f:
            raw = f.read()
        content = raw.decode("utf-8", errors="replace")
        m = re.search(r"<title>(.*?)</title>", content, re.DOTALL)
        title = m.group(1).strip() if m else "(제목 없음)"
        url = f"{SITE_DOMAIN}/{page_dir.name}/"
        count += 1
        lines.append(f"[{count:04d}] {url}")
        lines.append(f"       제목: {title}")
        lines.append("")

    lines.append("=" * 70)
    lines.append(f"  총 {count}개 URL")
    lines.append("=" * 70)

    OUTPUT_FILE.write_text("\n".join(lines), encoding="utf-8")
    print(f"완료! {count}개 URL → {OUTPUT_FILE}", flush=True)

if __name__ == "__main__":
    main()
