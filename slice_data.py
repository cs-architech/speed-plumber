#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
slice_data.py — 시간 기반 데이터 슬라이서
seo_pages_10000.csv를 읽어 경과 시간에 따라 current_build.csv로 저장.

누적 개수 공식:
  count = 10 + (경과_시간(hour) // 2) * 10
  → 최초 10개, 2시간마다 10개 추가, 하루 100개씩 누적
"""
import json
from datetime import datetime
from pathlib import Path

import pandas as pd

BASE_DIR   = Path(__file__).parent
META_FILE  = BASE_DIR / "deploy_meta.json"
SOURCE_CSV = BASE_DIR / "seo_pages_10000.csv"
OUTPUT_CSV = BASE_DIR / "current_build.csv"
COUNT_FILE = BASE_DIR / "build_count.txt"


def load_or_init_meta() -> dict:
    """deploy_meta.json 로드. START_DATE 없으면 지금 시각으로 초기화."""
    if META_FILE.exists():
        with open(META_FILE, encoding="utf-8") as f:
            meta = json.load(f)
    else:
        meta = {}

    if "START_DATE" not in meta:
        meta["START_DATE"] = datetime.now().isoformat()
        with open(META_FILE, "w", encoding="utf-8") as f:
            json.dump(meta, f, ensure_ascii=False, indent=2)
        print(f"  [초기화] START_DATE 설정됨: {meta['START_DATE']}")
        print(f"  [안내] deploy_meta.json을 git에 커밋하세요.")

    return meta


def calc_count(start_dt: datetime) -> int:
    """경과 시간을 기반으로 생성할 페이지 수 계산."""
    elapsed_hours = (datetime.now() - start_dt).total_seconds() / 3600
    return 10 + (int(elapsed_hours) // 2) * 10


def main() -> int:
    print("=" * 52)
    print("  slice_data.py  —  데이터 슬라이서")
    print("=" * 52)

    if not SOURCE_CSV.exists():
        print(f"\n[ERROR] {SOURCE_CSV.name} 파일이 없습니다.")
        print("  → 프로젝트 루트에 seo_pages_10000.csv를 준비해주세요.")
        return 1

    meta     = load_or_init_meta()
    start_dt = datetime.fromisoformat(meta["START_DATE"])
    count    = calc_count(start_dt)

    df    = pd.read_csv(SOURCE_CSV, encoding="utf-8-sig")
    total = len(df)
    count = min(count, total)

    df.iloc[:count].to_csv(OUTPUT_CSV, index=False, encoding="utf-8-sig")
    COUNT_FILE.write_text(str(count), encoding="utf-8")

    elapsed_h = (datetime.now() - start_dt).total_seconds() / 3600
    print(f"  시작일시  : {start_dt.strftime('%Y-%m-%d %H:%M')}")
    print(f"  경과시간  : {elapsed_h:.1f}시간 ({elapsed_h/24:.1f}일)")
    print(f"  생성 개수 : {count:,} / {total:,}")
    print(f"  출력 파일 : {OUTPUT_CSV.name}")
    print(f"  카운트    : {COUNT_FILE.name}  →  {count}")
    print("=" * 52)
    return 0


if __name__ == "__main__":
    import sys
    sys.exit(main())
