#!/usr/bin/env python3
"""
scripts/image_wash.py
─────────────────────────────────────────────────────────────────────────────
'03. 업로드 사진/' 폴더의 이미지를 세척하여 public/images/gallery/washed/ 에 저장.

세척 내용:
  1. EXIF 메타데이터 완전 제거 (개인정보·위치정보 차단)
  2. 미세 무작위 크롭 (1~4px) — 이미지 해시 고유화
  3. 품질 조정 (85~95 범위 무작위) — 파일 크기 최적화
  4. 썸네일 생성 (public/images/thumbs/ 720×540 이하)
  5. 파일명 seq 번호 재정리 (img_001.jpg …)

실행: python scripts/image_wash.py
      python scripts/image_wash.py --dry-run   # 실제 저장 없이 목록만 출력
"""

import os
import sys
import random
import argparse
import hashlib
from pathlib import Path

try:
    from PIL import Image
    PIL_OK = True
except ImportError:
    PIL_OK = False
    print("[ERROR] Pillow가 설치되어 있지 않습니다. pip install Pillow 를 실행하세요.", file=sys.stderr)
    sys.exit(1)

# ── 경로 설정 ────────────────────────────────────────────────────────────────
BASE       = Path(__file__).resolve().parent.parent
SRC_DIR    = BASE / "03. 업로드 사진"
DEST_DIR   = BASE / "public" / "images" / "gallery" / "washed"
THUMB_DIR  = BASE / "public" / "images" / "thumbs"
THUMB_SIZE = (720, 540)

SUPPORTED_EXT = {".jpg", ".jpeg", ".png", ".webp"}


def compute_seed(path: Path) -> int:
    """파일 이름 기반 재현 가능 시드"""
    return int(hashlib.md5(path.name.encode()).hexdigest()[:8], 16)


def wash_image(src_path: Path, dest_path: Path, thumb_path: Path, dry_run: bool, idx: int) -> bool:
    """단일 이미지 세척 + 저장. 성공 True, 실패 False."""
    try:
        with Image.open(src_path) as img:
            # EXIF 제거: 새 이미지 객체로 재생성
            if img.mode in ("RGBA", "P"):
                img = img.convert("RGB")
            elif img.mode != "RGB":
                img = img.convert("RGB")

            # 미세 크롭 (1~4px 랜덤)
            rng   = random.Random(compute_seed(src_path))
            cx    = rng.randint(1, 4)
            cy    = rng.randint(1, 4)
            w, h  = img.size
            if w > cx * 2 + 10 and h > cy * 2 + 10:
                img = img.crop((cx, cy, w - cx, h - cy))

            # 품질 (85~95)
            quality = rng.randint(85, 95)

            if not dry_run:
                dest_path.parent.mkdir(parents=True, exist_ok=True)
                img.save(dest_path, "JPEG", quality=quality, optimize=True, progressive=True)

                # 썸네일
                thumb_path.parent.mkdir(parents=True, exist_ok=True)
                thumb = img.copy()
                thumb.thumbnail(THUMB_SIZE, Image.LANCZOS)
                thumb.save(thumb_path, "JPEG", quality=80, optimize=True)

            print(f"  [{idx:04d}] {src_path.name}  →  {dest_path.name}  (q={quality}, crop={cx}x{cy})")
            return True

    except Exception as exc:
        print(f"  [SKIP] {src_path.name}: {exc}", file=sys.stderr)
        return False


def collect_sources() -> list[Path]:
    if not SRC_DIR.exists():
        print(f"[WARN] 소스 폴더 없음: {SRC_DIR}", file=sys.stderr)
        return []
    files = sorted(
        p for p in SRC_DIR.rglob("*")
        if p.is_file() and p.suffix.lower() in SUPPORTED_EXT
    )
    return files


def make_slug(region: str, keyword: str, idx: int) -> tuple[str, str]:
    """SEO-friendly 파일명 생성: {region}-{keyword}-작업사진-{idx:04d}.jpg"""
    safe_region  = region.replace(" ", "-").replace("/", "-")
    safe_keyword = keyword.replace(" ", "-").replace("/", "-")
    base  = f"{safe_region}-{safe_keyword}-작업사진-{idx:04d}.jpg"
    thumb = f"{safe_region}-{safe_keyword}-썸네일-{idx:04d}.jpg"
    return base, thumb


def main():
    parser = argparse.ArgumentParser(description="이미지 세척 스크립트")
    parser.add_argument("--dry-run", action="store_true", help="실제 저장 없이 목록만 출력")
    parser.add_argument("--force",   action="store_true", help="이미 변환된 파일도 재처리")
    parser.add_argument("--region",  default="서울경기",   help="파일명에 사용할 지역명 (기본: 서울경기)")
    parser.add_argument("--keyword", default="배관막힘",   help="파일명에 사용할 키워드 (기본: 배관막힘)")
    args = parser.parse_args()

    sources = collect_sources()
    if not sources:
        print("[image_wash] 처리할 이미지 없음. 건너뜀.")
        return

    print(f"[image_wash] {len(sources)}개 이미지 세척 시작 (dry_run={args.dry_run}, region={args.region}, keyword={args.keyword})")

    ok, skip = 0, 0
    for idx, src in enumerate(sources, 1):
        dest_name, thumb_name = make_slug(args.region, args.keyword, idx)
        dest  = DEST_DIR  / dest_name
        thumb = THUMB_DIR / thumb_name

        if not args.force and not args.dry_run and dest.exists():
            skip += 1
            continue

        success = wash_image(src, dest, thumb, args.dry_run, idx)
        if success:
            ok += 1
        # failed already printed

    total = ok + skip
    print(f"[image_wash] 완료: 처리={ok}, 스킵(기존)={skip}, 전체={total}")

    # gallery_manifest.json 생성 (Astro에서 import 가능)
    if not args.dry_run and ok > 0:
        manifest_path = DEST_DIR / "manifest.json"
        import json
        entries = [
            make_slug(args.region, args.keyword, i)[0]
            for i in range(1, total + 1)
            if (DEST_DIR / make_slug(args.region, args.keyword, i)[0]).exists()
        ]
        manifest_path.write_text(json.dumps(entries, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"[image_wash] manifest.json 저장: {manifest_path}")


if __name__ == "__main__":
    main()
