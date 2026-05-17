#!/usr/bin/env python3
"""
scripts/build_prepare.py
─────────────────────────────────────────────────────────────────────────────
빌드 전 준비 오케스트레이터.

수행 순서:
  1. image_wash.py  — 이미지 세척 (EXIF 제거, 크롭, 품질 최적화)

실행: python scripts/build_prepare.py
      python scripts/build_prepare.py --dry-run
"""

import subprocess
import sys
import time
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent


def run(script: str, extra_args: list[str] = []) -> int:
    script_path = BASE / "scripts" / script
    cmd = [sys.executable, str(script_path)] + extra_args
    print(f"\n[build_prepare] 실행: {' '.join(cmd)}")
    t0 = time.time()
    result = subprocess.run(cmd, cwd=str(BASE))
    elapsed = time.time() - t0
    status = "OK" if result.returncode == 0 else f"FAIL (exit {result.returncode})"
    print(f"[build_prepare] {script} → {status}  ({elapsed:.1f}s)")
    return result.returncode


def main():
    dry_run = "--dry-run" in sys.argv

    extra = ["--dry-run"] if dry_run else []

    print("=" * 60)
    print("[build_prepare] 빌드 준비 시작")
    print("=" * 60)

    rc = run("image_wash.py", extra)
    if rc != 0:
        print("[build_prepare] 이미지 세척 실패. 빌드를 중단합니다.", file=sys.stderr)
        sys.exit(rc)

    print("\n" + "=" * 60)
    print("[build_prepare] 빌드 준비 완료 OK")
    print("=" * 60)


if __name__ == "__main__":
    main()
