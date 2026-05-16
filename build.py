#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
build.py  ─  Python Static Site Generator
지역 CSV + 키워드 + 이미지 → SEO 최적화 index.html 생성
"""

import json
import math
import os
import random
import re
import shutil
import urllib.parse
from datetime import datetime
from io import BytesIO
from pathlib import Path

import pandas as pd
from jinja2 import Environment, FileSystemLoader
from PIL import Image

# ─── 경로 설정 ─────────────────────────────────────────────────────────────────
BASE_DIR        = Path(__file__).parent
OUTPUT_DIR      = BASE_DIR / "output"
IMAGES_OUT_DIR  = OUTPUT_DIR / "images"
FIRST_IMG_DIR   = BASE_DIR / "00. first image"
PHOTOS_DIR      = BASE_DIR / "03. 업로드 사진"
TEXT_DIR        = BASE_DIR / "02. 업로드 텍스트"
KEYWORDS_FILE   = BASE_DIR / "keywords.txt"
MID_KW_FILE     = BASE_DIR / "mid-keywords.txt"
REGION_CSV      = BASE_DIR / "region.csv"
REGIONS_JSON    = BASE_DIR / "regions_data.json"
TEMPLATE_FILE   = "template.html"

# ─── 사이트 설정 ───────────────────────────────────────────────────────────────
PHONE               = "010-6522-5759"
SITE_NAME           = "하수구막힘 전문"
GOOGLE_APPS_URL     = (
    "https://script.google.com/macros/s/"
    "AKfycbyDVeRRffY40-PLJB3AXFWpJVqyQ9yxIJVvQj_Jxnm6x528J5HX-t6CVG_MDmfdSey0/exec"
)
REGION_BLOCK_COUNT  = 13  # 생성할 지역 블록 수 (주요 1 + 점검가능 12)
GALLERY_RANGE       = (5, 11)
KEYWORDS_POOL       = ['싱크대막힘', '변기막힘', '배관막힘', '하수구막힘',
                       '우수관막힘', '하수구역류', '배관고압세척', '하수구뚫음']

# ─── Spintax 풀 ────────────────────────────────────────────────────────────────
TITLE_POOL = [
    "{region} {keyword} 업체 점검가능 지역 리스트",
    "{region} 지역 {keyword} 서비스 가능 업체 현황",
    "{keyword} 전문 업체 · {region} 점검 가능 구역 안내",
    "{region} 인근 {keyword} 출장 가능 지역 목록",
    "{keyword} 업체 서비스 지역 ({region} 기준)",
    "{region} {keyword} 담당 가능 지역 현황 정리",
]

DESC_POOL = [
    "{keyword} 외 등 {count}+3개 점검 가능 지역을 찾았고, 이 중 최대 {count}개를 확인할 수 있도록 정리했습니다.",
    "총 {count}+3개 이상의 {keyword} 서비스 가능 지역 중 대표 {count}개 지역을 선별하여 안내드립니다.",
    "{keyword} 출장 가능 지역이 {count}+3곳 이상 확인되었으며, 주요 {count}개 지역 정보를 아래에 정리하였습니다.",
    "검색된 {keyword} 점검 가능 지역 {count}+3개 중 가까운 순으로 {count}개 지역을 추려 제공합니다.",
    "{count}개 이상의 {keyword} 서비스 지역을 확인했으며, 그 중 {count}곳의 상세 정보를 아래에서 확인하실 수 있습니다.",
    "{keyword} 업체가 담당하는 {count}+3개 구역 데이터를 분석하여 핵심 {count}개 지역만 모아드렸습니다.",
]

CATEGORY_POOL = [
    "건설업 > 전문건설업 / 배관·냉난방공사",
    "전문건설업 | 배관설비·냉난방 시공",
    "건설업종 : 배관공사 전문 (냉난방 포함)",
    "업종 분류 : 배관·위생설비 전문건설",
    "등록업종 > 건설 / 배관·위생설비공사",
    "사업 분야 : 배관막힘·냉난방설비 전문",
]

# 동의어 치환 테이블 (SEO 유사문서 회피)
SYNONYMS = {
    "해결": ["처리", "완료", "조치", "수습"],
    "전문가": ["기술자", "전문 기사", "숙련 기사"],
    "신속": ["빠르게", "즉시", "즉각"],
    "확인": ["점검", "진단", "검토"],
    "작업": ["시공", "조치", "서비스"],
    "배관": ["관로", "파이프", "수도관"],
    "막힘": ["폐색", "차단", "정체"],
    "역류": ["거꾸로 흐름", "백플로우"],
    "악취": ["불쾌한 냄새", "이취"],
    "고압세척": ["고압 청소", "워터젯 세척"],
    "뚫": ["통수", "소통"],
    "스케일링": ["찌꺼기 제거", "관로 청소"],
}

# 텍스트 내 치환할 지역명 목록
KNOWN_REGIONS = [
    "안산", "수원", "군포", "시흥", "안양", "의왕", "광명", "부천",
    "화성", "오산", "인천", "성남", "용인", "종로구", "중구",
    "고양", "과천", "하남", "의정부", "남양주",
]
KNOWN_KEYWORDS = [
    "하수구막힘", "배관막힘", "싱크대막힘", "변기막힘",
    "하수구역류", "배관고압세척", "하수구뚫음", "배관뚫음",
    "하수구뚫는업체", "싱크대역류",
]

# ─── 유틸 ──────────────────────────────────────────────────────────────────────

def haversine(lat1, lng1, lat2, lng2) -> float:
    R = 6371.0
    d_lat = math.radians(lat2 - lat1)
    d_lng = math.radians(lng2 - lng1)
    a = (math.sin(d_lat / 2) ** 2
         + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2))
         * math.sin(d_lng / 2) ** 2)
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


def load_lines(path: Path) -> list[str]:
    with open(path, encoding="utf-8") as f:
        return [ln.strip() for ln in f if ln.strip()]


# ─── 지역 데이터 ──────────────────────────────────────────────────────────────

def load_regions() -> pd.DataFrame:
    df = pd.read_csv(REGION_CSV, encoding="utf-8-sig", header=0,
                     names=["시군구", "읍면동", "위도", "경도"])
    df["위도"] = pd.to_numeric(df["위도"], errors="coerce")
    df["경도"] = pd.to_numeric(df["경도"], errors="coerce")
    return df.dropna(subset=["위도", "경도"]).reset_index(drop=True)


def region_fullname(row) -> str:
    emd = str(row.get("읍면동", "") or "").strip()
    if emd and emd.lower() != "nan":
        return f"{row['시군구']} {emd}"
    return str(row["시군구"])


def load_regions_json() -> list[dict] | None:
    """regions_data.json 이 있으면 로드, 없으면 None 반환."""
    if REGIONS_JSON.exists():
        with open(REGIONS_JSON, encoding="utf-8") as f:
            return json.load(f)
    return None


def build_region_blocks(df: pd.DataFrame, main_keyword: str, mid_kw_lines: list[str]) -> list[dict]:
    # ── regions_data.json 우선 사용 ──────────────────────────────────────────
    json_data = load_regions_json()
    if json_data:
        blocks = []
        alt_kw_pool = [k for k in KEYWORDS_POOL if k != main_keyword]
        for i, entry in enumerate(json_data):
            name    = entry["name"]
            lat     = float(entry["lat"])
            lng     = float(entry["lon"])
            area_kw = main_keyword if i == 0 else alt_kw_pool[(i - 1) % len(alt_kw_pool)]
            q_search = urllib.parse.quote(f"{name} {area_kw} 업체")
            blocks.append({
                "name":        name,
                "jibun_addr":  entry.get("jibun_addr", ""),
                "road_addr":   entry.get("road_addr", ""),
                "lat":         round(lat, 6),
                "lng":         round(lng, 6),
                "keyword":     area_kw,
                "mid_kw":      random.choice(mid_kw_lines),
                "category":    entry.get("category", random.choice(CATEGORY_POOL)),
                "weather":     entry.get("weather", ""),
                "google_url":  f"https://www.google.com/maps/search/{q_search}",
                "naver_url":   f"https://map.naver.com/v5/search/{q_search}",
                "is_primary":  bool(entry.get("is_primary", i == 0)),
            })
        return blocks

    # ── fallback: region.csv 랜덤 선택 ────────────────────────────────────────
    primary_idx = random.choice(df.index.tolist())
    primary = df.loc[primary_idx]
    p_lat, p_lng = float(primary["위도"]), float(primary["경도"])

    others = df[df.index != primary_idx].copy()
    others["_dist"] = others.apply(
        lambda r: haversine(p_lat, p_lng, r["위도"], r["경도"]), axis=1
    )
    nearby = others.nsmallest(REGION_BLOCK_COUNT - 1, "_dist")

    blocks = []
    for i, (_, row) in enumerate([(None, primary)] + list(nearby.iterrows())):
        name = region_fullname(row)
        lat  = float(row["위도"])
        lng  = float(row["경도"])
        alt_kw_pool = [k for k in KEYWORDS_POOL if k != main_keyword]
        area_kw = main_keyword if i == 0 else alt_kw_pool[(i - 1) % len(alt_kw_pool)]
        q_search = urllib.parse.quote(f"{name} {area_kw} 업체")
        blocks.append({
            "name":        name,
            "jibun_addr":  "",
            "road_addr":   "",
            "lat":         round(lat, 6),
            "lng":         round(lng, 6),
            "keyword":     area_kw,
            "mid_kw":      random.choice(mid_kw_lines),
            "category":    random.choice(CATEGORY_POOL),
            "weather":     "",
            "google_url":  f"https://www.google.com/maps/search/{q_search}",
            "naver_url":   f"https://map.naver.com/v5/search/{q_search}",
            "is_primary":  i == 0,
        })
    return blocks


# ─── 이미지 처리 ──────────────────────────────────────────────────────────────

def wash_and_compress(src: Path, dst: Path, max_kb: int = 100):
    """EXIF 제거 + 미세 크롭(해시 변경) + 100KB 이하 압축 → 단일 저장."""
    target = max_kb * 1024
    with Image.open(src) as img:
        img = img.convert("RGB")
        # EXIF 제거: 픽셀 데이터 새 이미지 복사
        clean = Image.new("RGB", img.size)
        clean.putdata(list(img.getdata()))  # type: ignore[arg-type]
        # 미세 크롭 (1~3px) → 해시 변경
        w, h = clean.size
        clean = clean.crop((
            random.randint(1, 3), random.randint(1, 3),
            w - random.randint(1, 3), h - random.randint(1, 3),
        ))
        # 100KB 이하가 될 때까지 품질 단계적 하향
        for quality in [85, 75, 65, 55, 45, 35]:
            buf = BytesIO()
            clean.save(buf, format="JPEG", quality=quality, optimize=True)
            if buf.tell() <= target:
                dst.write_bytes(buf.getvalue())
                return
        # 여전히 크면 해상도도 축소
        max_dim = 1200
        if max(clean.size) > max_dim:
            clean.thumbnail((max_dim, max_dim), Image.LANCZOS)
        buf = BytesIO()
        clean.save(buf, format="JPEG", quality=35, optimize=True)
        dst.write_bytes(buf.getvalue())


def select_diverse_photos(n: int) -> list[Path]:
    """시리즈별로 1장씩 돌아가며 다양하게 선택"""
    exts = {".jpg", ".jpeg", ".png"}
    all_photos = [p for p in PHOTOS_DIR.iterdir() if p.suffix.lower() in exts]
    if not all_photos:
        return []

    groups: dict[str, list[Path]] = {}
    for p in all_photos:
        key = re.sub(r"\(\d+\)\s*$", "", p.stem).strip()
        groups.setdefault(key, []).append(p)

    keys = list(groups.keys())
    random.shuffle(keys)
    selected: list[Path] = []
    i = 0
    while len(selected) < n and keys:
        key = keys[i % len(keys)]
        pool = [p for p in groups[key] if p not in selected]
        if pool:
            selected.append(random.choice(pool))
        i += 1
        if i > len(keys) * 4:
            break
    return selected[:n]


def process_gallery_named(img_dir: Path, region: str, keyword: str) -> list[str]:
    """이미지 세탁 + 100KB 압축 → '{region} {keyword} 업체 긴급출동(N).jpg' 단일 저장."""
    img_dir.mkdir(parents=True, exist_ok=True)
    n = random.randint(*GALLERY_RANGE)
    photos = select_diverse_photos(n)
    paths: list[str] = []
    for i, src in enumerate(photos):
        fname = f"{region} {keyword} 업체 긴급출동({i + 1}).jpg"
        dst   = img_dir / fname
        try:
            wash_and_compress(src, dst, max_kb=100)
            paths.append(f"images/{fname}")
        except Exception as e:
            print(f"  [WARN] {src.name}: {e}")
    return paths


# ─── 첫 번째 이미지 ───────────────────────────────────────────────────────────

def copy_first_images() -> list[str]:
    dst_dir = IMAGES_OUT_DIR / "first"
    dst_dir.mkdir(parents=True, exist_ok=True)
    exts = {".jpg", ".jpeg", ".png", ".webp", ".gif"}
    imgs = sorted(
        [p for p in FIRST_IMG_DIR.iterdir() if p.suffix.lower() in exts],
        key=lambda p: p.name,
    )
    paths = []
    for img in imgs:
        dst = dst_dir / img.name
        shutil.copy2(img, dst)
        paths.append(f"images/first/{img.name}")
    return paths


# ─── 후기 텍스트 처리 ─────────────────────────────────────────────────────────

def apply_synonyms(text: str) -> str:
    for word, syns in SYNONYMS.items():
        if word in text and random.random() > 0.45:
            # 첫 1~2회만 치환
            replacement = random.choice(syns)
            text = text.replace(word, replacement, random.randint(1, 2))
    return text


def process_review(region: str, keyword: str) -> list[str]:
    txt_files = list(TEXT_DIR.glob("*.txt"))
    if not txt_files:
        return ["후기 내용을 불러올 수 없습니다."]

    raw = (random.choice(txt_files)).read_text(encoding="utf-8")

    # 전화번호 제거
    raw = re.sub(r"0\d{1,2}[-\s]?\d{3,4}[-\s]?\d{4}", "", raw)
    # "출장비 무료" 제거
    raw = re.sub(r"출장비\s*무료[^.。]*[.。]?", "", raw)

    # 기존 지역명·키워드 → 플레이스홀더
    for r in sorted(KNOWN_REGIONS, key=len, reverse=True):
        raw = raw.replace(r, "__REGION__", 1)
    for k in sorted(KNOWN_KEYWORDS, key=len, reverse=True):
        raw = raw.replace(k, "__KW__", 1)

    # 문단 분리 → 셔플 (앞뒤 1개씩 고정)
    paras = [p.strip() for p in raw.split("\n\n") if p.strip()]
    if len(paras) > 3:
        head, tail = paras[:1], paras[-1:]
        mid = paras[1:-1]
        random.shuffle(mid)
        paras = head + mid + tail

    # 동의어 치환
    paras = [apply_synonyms(p) for p in paras]

    # 지역/키워드 삽입 (2~3곳 사이사이)
    inject_at = random.sample(range(len(paras)), min(3, len(paras)))
    for pos in inject_at:
        paras[pos] = f"{region} {keyword} – " + paras[pos]

    # 플레이스홀더 → 실제 값
    result = []
    for p in paras:
        p = p.replace("__REGION__", region).replace("__KW__", keyword)
        result.append(p)

    return result


# ─── 단일 페이지 빌드 ─────────────────────────────────────────────────────────

def build_one(page_dir: Path, keywords: list[str], mid_kw_lines: list[str],
              df, env, tpl, first_images: list[str], page_num: int):
    """랜덤 지역·키워드 조합으로 index.html 1개 생성 (이미지 단일 폴더, 100KB 압축)."""
    page_dir.mkdir(parents=True, exist_ok=True)
    img_dir = page_dir / "images"

    main_keyword  = random.choice(keywords[:6])
    region_blocks = build_region_blocks(df, main_keyword, mid_kw_lines)
    primary_name  = region_blocks[0]["name"]

    title_text = random.choice(TITLE_POOL).format(region=primary_name, keyword=main_keyword)
    desc_text  = random.choice(DESC_POOL).format(keyword=main_keyword, count=REGION_BLOCK_COUNT)

    # 이미지 세탁: 단일 폴더, 한글 파일명, 100KB 이하
    gallery_images = process_gallery_named(img_dir, primary_name, main_keyword)
    main_gallery   = gallery_images[:3]
    sub_gallery    = [(p, p) for p in gallery_images[3:]]  # 썸네일=동일파일, CSS로 축소

    # 상단 이미지 상대경로
    first_imgs_rel = [f"../images/first/{Path(p).name}" for p in first_images]

    review_paras = process_review(primary_name, main_keyword)

    html = tpl.render(
        phone           = PHONE,
        site_name       = SITE_NAME,
        region          = primary_name,
        keyword         = main_keyword,
        title_text      = title_text,
        desc_text       = desc_text,
        region_blocks   = region_blocks,
        first_images    = first_imgs_rel,
        main_gallery    = main_gallery,
        sub_gallery     = sub_gallery,
        review_paras    = review_paras,
        google_apps_url = GOOGLE_APPS_URL,
        build_time      = datetime.now().strftime("%Y-%m-%d %H:%M"),
        block_count     = len(region_blocks),
    )

    out = page_dir / "index.html"
    out.write_text(html, encoding="utf-8")
    print(f"  [page {page_num}] {primary_name} / {main_keyword}  gallery={len(gallery_images)}")
    return out


# ─── 메인 빌드 ────────────────────────────────────────────────────────────────

def build(test_count: int = 0):
    """
    test_count > 0 : test_count개 테스트 페이지만 output/test-N/ 에 생성
    test_count == 0: 단일 페이지 output/index.html 생성 (기존 동작)
    """
    print("=" * 55)
    print("  build.py  -  Static Site Generator")
    if test_count:
        print(f"  [TEST MODE]  {test_count}개 페이지 생성")
    print("=" * 55)

    OUTPUT_DIR.mkdir(exist_ok=True)
    IMAGES_OUT_DIR.mkdir(exist_ok=True)

    # 공통 데이터 로드 (1회)
    print("[1/4] 데이터 로드 중...")
    keywords     = load_lines(KEYWORDS_FILE)
    mid_kw_lines = load_lines(MID_KW_FILE)
    df           = load_regions()

    print("[2/4] 상단 이미지 복사 중...")
    first_images = copy_first_images()   # output/images/first/

    print("[3/4] Jinja2 환경 준비 중...")
    env = Environment(
        loader=FileSystemLoader(str(BASE_DIR)),
        autoescape=False,
        keep_trailing_newline=True,
    )
    env.filters["nl2br"] = lambda v: v.replace("\n", "<br>")
    tpl = env.get_template(TEMPLATE_FILE)

    print("[4/4] 페이지 생성 중...")

    if test_count:
        # ── 테스트 모드: N개 페이지 → output/test-1/ … output/test-N/
        generated = []
        for i in range(1, test_count + 1):
            page_dir = OUTPUT_DIR / f"test-{i}"
            out = build_one(page_dir, keywords, mid_kw_lines, df, env, tpl,
                            first_images, i)
            generated.append(out)

        print("-" * 55)
        print(f"[DONE] {test_count}개 테스트 페이지 생성 완료")
        for p in generated:
            print(f"  -> {p}")
    else:
        # ── 단일 모드: output/index.html (기존 동작)
        # 단일 모드에서는 이미지를 output/images/ 바로 아래 저장
        main_keyword  = random.choice(keywords[:6])
        region_blocks = build_region_blocks(df, main_keyword, mid_kw_lines)
        primary_name  = region_blocks[0]["name"]

        title_text = random.choice(TITLE_POOL).format(
            region=primary_name, keyword=main_keyword
        )
        desc_text = random.choice(DESC_POOL).format(
            keyword=main_keyword, count=REGION_BLOCK_COUNT
        )

        # 이미지: output/images/ 단일 폴더, 100KB, 한글 파일명
        gallery_images = process_gallery_named(IMAGES_OUT_DIR, primary_name, main_keyword)
        main_gallery   = gallery_images[:3]
        sub_gallery    = [(p, p) for p in gallery_images[3:]]
        review_paras   = process_review(primary_name, main_keyword)

        html = tpl.render(
            phone           = PHONE,
            site_name       = SITE_NAME,
            region          = primary_name,
            keyword         = main_keyword,
            title_text      = title_text,
            desc_text       = desc_text,
            region_blocks   = region_blocks,
            first_images    = first_images,
            main_gallery    = main_gallery,
            sub_gallery     = sub_gallery,
            review_paras    = review_paras,
            google_apps_url = GOOGLE_APPS_URL,
            build_time      = datetime.now().strftime("%Y-%m-%d %H:%M"),
            block_count     = len(region_blocks),
        )

        out = OUTPUT_DIR / "index.html"
        out.write_text(html, encoding="utf-8")
        print(f"[OK] {out}  ({primary_name} / {main_keyword})")
        print(f"     gallery={len(gallery_images)}")


if __name__ == "__main__":
    import sys
    # 인자로 숫자를 넘기면 그 수만큼 테스트 페이지 생성
    # 예: python build.py 3   → 테스트 3페이지
    #     python build.py      → 단일 index.html
    count = int(sys.argv[1]) if len(sys.argv) > 1 else 0
    build(test_count=count)
