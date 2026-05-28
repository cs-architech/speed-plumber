#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
netlify_deploy.py — Netlify 배포 슬라이서
pages_bank/에서 시간 기반으로 N개 페이지를 output/으로 복사.
Python 표준 라이브러리만 사용 (의존성 설치 불필요).
"""
import json
import shutil
from datetime import datetime
from pathlib import Path

BASE_DIR    = Path(__file__).parent
BANK_DIR    = BASE_DIR / "pages_bank"
OUTPUT_DIR  = BASE_DIR / "output"
META_FILE   = BASE_DIR / "deploy_meta.json"
SITE_DOMAIN = "https://speed-plumber.netlify.app"


def calc_count(start_dt: datetime) -> int:
    elapsed_hours = (datetime.now() - start_dt).total_seconds() / 3600
    return 10 + (int(elapsed_hours) // 2) * 10


def main() -> int:
    print("=" * 52)
    print("  netlify_deploy.py  —  배포 슬라이서")
    print("=" * 52)

    if not META_FILE.exists():
        print("[ERROR] deploy_meta.json 없음 — 로컬에서 slice_data.py를 먼저 실행하세요.")
        return 1
    if not BANK_DIR.exists():
        print("[ERROR] pages_bank/ 없음 — 로컬에서 python build.py bank N을 먼저 실행하세요.")
        return 1

    with open(META_FILE, encoding="utf-8") as f:
        meta = json.load(f)
    start_dt = datetime.fromisoformat(meta["START_DATE"])
    count    = calc_count(start_dt)

    pages = sorted(BANK_DIR.glob("page-????"))
    total = len(pages)
    count = min(count, total)

    # output/ 초기화
    if OUTPUT_DIR.exists():
        shutil.rmtree(OUTPUT_DIR)
    OUTPUT_DIR.mkdir()

    # 공유 이미지 복사 (한 번만)
    bank_img = BANK_DIR / "images"
    if bank_img.exists():
        shutil.copytree(str(bank_img), str(OUTPUT_DIR / "images"))

    # favicon 루트 복사
    favicon_src = BANK_DIR / "images" / "pavicon.png"
    if favicon_src.exists():
        shutil.copy2(favicon_src, OUTPUT_DIR / "favicon.png")

    # 카테고리 페이지 복사 (한글 디렉토리)
    cat_dirs = ["배관", "하수구막힘", "싱크대막힘", "변기막힘", "우수관막힘", "고압세척"]
    for cat in cat_dirs:
        cat_src = BANK_DIR / cat
        if cat_src.exists():
            shutil.copytree(str(cat_src), str(OUTPUT_DIR / cat))

    # N개 페이지 HTML 복사
    for page_dir in pages[:count]:
        dst = OUTPUT_DIR / page_dir.name
        dst.mkdir()
        shutil.copy2(page_dir / "index.html", dst / "index.html")

    # sitemap.xml 생성
    today = datetime.now().strftime("%Y-%m-%d")
    lines = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">',
    ]
    for page_dir in pages[:count]:
        url = f"{SITE_DOMAIN}/{page_dir.name}/"
        lines.append(
            f'  <url><loc>{url}</loc><lastmod>{today}</lastmod>'
            f'<changefreq>weekly</changefreq><priority>0.8</priority></url>'
        )
    lines.append("</urlset>")
    (OUTPUT_DIR / "sitemap.xml").write_text("\n".join(lines), encoding="utf-8")

    # robots.txt 생성 (Googlebot, Yeti 명시)
    robots = "\n".join([
        "User-agent: *",
        "Allow: /",
        "",
        "User-agent: Googlebot",
        "Allow: /",
        "",
        "User-agent: Yeti",
        "Allow: /",
        "",
        f"Sitemap: {SITE_DOMAIN}/sitemap.xml",
        "",
    ])
    (OUTPUT_DIR / "robots.txt").write_text(robots, encoding="utf-8")

    # 루트 index.html — page-0001 내용을 그대로 복사 (canonical은 page-0001/ 유지)
    if count > 0:
        shutil.copy2(pages[0] / "index.html", OUTPUT_DIR / "index.html")

    # 404.html — 존재하지 않는 경로 접근 시 표시
    not_found_html = f"""<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>페이지를 찾을 수 없습니다</title>
<style>body{{font-family:sans-serif;text-align:center;padding:80px 20px;background:#f5f7fa}}h1{{font-size:3rem;color:#1a237e}}p{{color:#555;margin:16px 0}}a{{color:#1a237e;font-weight:700}}</style>
</head>
<body>
<h1>404</h1>
<p>요청하신 페이지를 찾을 수 없습니다.</p>
<p><a href="/">홈으로 돌아가기</a></p>
</body>
</html>"""
    (OUTPUT_DIR / "404.html").write_text(not_found_html, encoding="utf-8")

    # 웹마스터 인증 파일 복사 (webmaster_files/ 폴더에 파일 넣으면 자동 배포)
    webmaster_dir = BASE_DIR / "webmaster_files"
    if webmaster_dir.exists():
        for vf in webmaster_dir.iterdir():
            if vf.is_file() and vf.suffix in {".html", ".txt"}:
                shutil.copy2(vf, OUTPUT_DIR / vf.name)
                print(f"  [인증파일] {vf.name} 복사 완료")

    elapsed_h = (datetime.now() - start_dt).total_seconds() / 3600
    print(f"  시작일시  : {start_dt.strftime('%Y-%m-%d %H:%M')}")
    print(f"  경과시간  : {elapsed_h:.1f}시간 ({elapsed_h / 24:.1f}일)")
    print(f"  배포 페이지: {count:,} / {total:,}")
    print(f"  sitemap  : {count}개 URL 등록")
    print(f"  robots   : Googlebot, Yeti 허용")
    print("=" * 52)
    return 0


if __name__ == "__main__":
    import sys
    sys.exit(main())
