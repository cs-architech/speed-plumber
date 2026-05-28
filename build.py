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
FAQ_FILE        = BASE_DIR / "faq6000.txt"

# ─── 사이트 설정 ───────────────────────────────────────────────────────────────
PHONE               = "1866-2449"
SITE_NAME           = "하수구막힘 전문"
GOOGLE_APPS_URL     = (
    "https://script.google.com/macros/s/"
    "AKfycbxcmiQ8bvCcxBwjwRfAnZM3ke7LtoC2BfjyeSu-hRymbJ827RWiAWEPb79jBfe-yeF8/exec"
)
REGION_BLOCK_COUNT  = 13  # 생성할 지역 블록 수 (주요 1 + 점검가능 12)
GALLERY_RANGE       = (5, 11)
KEYWORDS_POOL       = ['싱크대막힘', '변기막힘', '배관막힘', '하수구막힘',
                       '우수관막힘', '하수구역류', '배관고압세척', '하수구뚫음']
SITE_DOMAIN         = "https://speed-plumber.netlify.app"

# ─── 웹마스터 인증 코드 ────────────────────────────────────────────────────────
# Google Search Console → 설정 → 소유권 인증 → HTML 태그 → content 값 입력
GOOGLE_SITE_VERIFICATION = "Qfw9m9Ndmn1PzY6iz0Lobbm7jfBXskCQL6HJJoYOYCY"
# Naver Search Advisor → 사이트 추가 → HTML 태그 → content 값 입력
NAVER_SITE_VERIFICATION  = "abed9af5d3f4df622eeac2d2fe017acc3cbdaf26"

# ─── 1. 사용자 제공 데이터 (블록 조립형 무한 조합 스핀택스) ─────────────────────

TITLE_PREFIXES = [
    "", "[긴급]", "[당일출동]", "갑작스러운", "답답한", "골치 아픈", 
    "타업체 포기건,", "급하게 알아본", "자꾸 반복되는", "새벽에 터진", 
    "지긋지긋한", "해결 안 되는", "비용 걱정 없는", "가장 빠른", 
    "후기 좋은", "실패 없는", "눈탱이 없는", "지인 추천", 
    "셀프로 안 되는", "자주 발생하는"
]

TITLE_FORMATS = [
    "{prefix} {region} {keyword} {action} {suffix}",           
    "{prefix} [{region}] {keyword} {action} {suffix}",         
    "{prefix} {region} 주변 {keyword} {action} {suffix}",      
    "{prefix} {keyword} 문제, {region} {action} {suffix}",     
    "{region} 지역 {keyword} {prefix} {action} {suffix}",      
    "[{region} 출장] {prefix} {keyword} {action} {suffix}"     
]

TITLE_ACTIONS = [
    "확실한 해결 사례", "속 시원한 조치 방법", "비용 및 작업 과정 안내", 
    "30분 내 당일 방문 정보", "전문가의 리얼 시공기", "원인부터 찾는 점검", 
    "정직한 비용 처리 결과", "최신 장비로 소통 완료", "해결 비결 전격 공개", 
    "출장 서비스 추천 목록", "눈속임 없는 진짜 리뷰", "직접 겪어본 생생한 경험", 
    "타업체 실패건 100% 성공", "증상별 맞춤 해결 가이드", "초고속 방문 서비스", 
    "비용 폭탄 피하는 노하우", "정가제 출장 리스트", "작업 소요 시간 총정리", 
    "예방부터 스케일링까지", "근본 원인 완벽 차단", "하자 없는 꼼꼼한 시공", 
    "거품 뺀 합리적인 선택", "최상급 장비 보유 현황", "단골이 많은 진짜 이유", 
    "이용 고객 만족도 1위", "믿고 맡기는 안심 서비스", "현장 검증 완료", 
    "덤터기 없는 양심 시공", "내돈내산 찐 시공기", "배관 내시경 꼼꼼 점검"
]

TITLE_SUFFIXES = [
    "", "(긴급출동 가능)", "강력 추천",  "(서울/경기 긴급출동)", "총정리", "알아보기", 
    "공개합니다", "확인하세요", "꿀팁", "비교 분석", "안내", 
    "(당일 조치)", "필독", "리스트", "대공개", "주의할 점"
]

# 제목 54,000개 자동 생성
TITLE_POOL = []
for prefix in TITLE_PREFIXES:
    for fmt in TITLE_FORMATS:
        for action in TITLE_ACTIONS:
            for suffix in TITLE_SUFFIXES:
                raw_text = fmt.format(
                    prefix=prefix, 
                    region="{region}", 
                    keyword="{keyword}", 
                    action=action, 
                    suffix=suffix
                )
                TITLE_POOL.append(" ".join(raw_text.split()))

DESC_PART1 = [
    "오늘은 {region} 인근에서 {keyword} 문제로 스트레스 받으시는 분들을 위해 준비했습니다.",
    "{keyword} 때문에 갑자기 당황하셨나요?",
    "안녕하세요! 최근 {region} 지역에서 {keyword} 관련 문의가 정말 많아졌는데요.",
    "{region}에서 {keyword} 관련 정보를 찾고 계신다면 꼭 끝까지 읽어주세요!",
    "{keyword} 방치하면 나중에 더 큰 공사비가 깨질 수 있습니다.",
    "요즘 {region} 주변 {keyword} 비용이 천차만별이죠?",
    "물은 안 내려가고 악취까지... {keyword} 정말 답답하시죠?",
    "지금 당장 {region} 지역에 {keyword} 전문가가 필요하신가요?",
    "타업체에서 뚫지 못해 포기한 {keyword}도 문제없습니다!",
    "본 포스팅에서는 {region} 기준 {keyword} 출장 서비스 지역을 총정리합니다.",
    "검색된 {keyword} 점검 가능 구역 {count_plus_3}개 중 핵심만 추렸습니다.",
    "{keyword} 작업 전 반드시 확인해야 할 지역별 출장 현황입니다.",
    "총 {count_plus_3}개 이상의 {region} {keyword} 출장 가능 지역 데이터를 분석했습니다.",
    "잦은 {keyword} 현상으로 업체를 여러 번 부르셨다면 이 글에 주목해 주세요.",
    "야간이나 주말에 갑자기 터진 {keyword} 문제, 이제 걱정 마세요."
]

DESC_PART2 = [
    "주변에 {count_plus_3}개가 넘는 업체가 있지만,",
    "{region} 주변 서비스 가능 지역 {count_plus_3}곳을 직접 조사해 보고,",
    "타업체에서 실패한 건도 해결 가능한 {count_plus_3}개 이상의 네트워크 중,",
    "덤터기 쓰지 않고 합리적으로 조치할 수 있는 {count_plus_3}개의 출장 구역 중,",
    "{region} 전역 {count_plus_3}곳을 담당하는 배관 기사님들의 작업 동선을 분석하여,",
    "고객님들의 합리적인 선택을 돕기 위해 {count_plus_3}개의 점검 가능 구역 데이터를 추합했고,",
    "{region} 지역에서 당장 조치가 필요한 분들을 위해, {count_plus_3}개의 긴급출동 가능 권역을 비교하여,",
    "시간 낭비하지 마시라고 총 {count_plus_3}개의 출장 가능 리스트 중,",
    "{region} 인근 {count_plus_3}개 거점의 특수 장비 배차 현황을 파악하여,",
    "현재 검색된 {count_plus_3}개의 서비스 권역 데이터를 바탕으로,",
    "{region} 고객님들이 가장 많이 찾으시는 데이터를 검토하여,",
    "{region} 업체가 전담하는 {count_plus_3}개 구역의 출장 이력을 바탕으로,",
    "작업 소요 시간과 이동 동선이 가장 효율적인 곳을 찾기 위해,",
    "근본 원인을 잡아내는 업체를 선별하기 위해 {count_plus_3}개 거점을 확인했고,",
    "비용부터 A/S까지 확실한 업체를 찾기 위해 {count_plus_3}개의 데이터를 꼼꼼히 비교했습니다."
]

DESC_PART3 = [
    "그중에서도 가장 평점이 좋고 출장이 빠른 핵심 {count}곳의 정보를",
    "가장 믿을 수 있는 {count}개 출장 구역의 리스트를",
    "가장 가까운 {count}곳의 상세 정보를",
    "대표적인 {count}개 지역의 상세 서비스 현황을",
    "30분 내 당일 방문이 가능한 {count}개 주요 지역 리스트를",
    "이 중 출장비 걱정 없는 {count}곳의 찐 정보를",
    "가장 신속하게 방문하는 베스트 {count}곳의 위치를",
    "실시간 점검이 가능한 베스트 {count}곳만 엄선해서",
    "확실하게 해결해 줄 수 있는 {count}개의 핵심 출장 지역을",
    "가까운 순으로 {count}개 지역을 우선적으로 추려",
    "핫스팟으로 떠오르는 {count}곳의 상세 정보를",
    "가장 만족도가 높은 핵심 {count}개 권역만 깔끔하게",
    "가장 효율적인 대표 {count}개 지역을 선별하여",
    "고객 만족도가 가장 높은 {count}곳의 리스트를",
    "실시간 배차가 가능한 상위 {count}개 지역을"
]

DESC_PART4 = [
    "꼼꼼하게 비교해 드릴게요.",
    "알기 쉽게 정리해 봤습니다.",
    "투명하게 공개합니다.",
    "상세히 안내해 드립니다.",
    "지금 바로 공유해 드립니다.",
    "낱낱이 파헤쳐 보겠습니다.",
    "아래에 정리해 두었습니다.",
    "지금 바로 확인해 보세요.",
    "깔끔하게 요약해 드립니다.",
    "우선적으로 안내해 드립니다.",
    "밑에서 바로 확인하실 수 있습니다.",
    "확실하게 짚어 드리겠습니다.",
    "가감 없이 알려드립니다.",
    "빠르게 요약정리해 드립니다.",
    "한눈에 보기 쉽게 제공합니다."
]

# 설명 50,625개 자동 생성
DESC_POOL = [
    f"{d1} {d2} {d3} {d4}" 
    for d1 in DESC_PART1 
    for d2 in DESC_PART2 
    for d3 in DESC_PART3 
    for d4 in DESC_PART4
]

CATEGORY_POOL = [
    "건설업 > 전문건설업 / 배관·냉난방공사",
    "전문건설업 | 배관설비·냉난방 시공",
    "건설업종 : 배관공사 전문 (냉난방 포함)",
    "업종 분류 : 배관·위생설비 전문건설",
    "등록업종 > 건설 / 배관·위생설비공사",
    "사업 분야 : 배관막힘·냉난방설비 전문"
]

SYNONYMS = {
    "해결": ["처리", "완료", "조치", "수습", "마무리"],
    "전문가": ["기술자", "전문 기사", "숙련 기사", "베테랑", "전문팀"],
    "신속": ["빠르게", "즉시", "즉각", "지체 없이", "총알처럼"],
    "확인": ["점검", "진단", "검토", "파악", "테스트"],
    "작업": ["시공", "조치", "서비스", "공사", "케어"],
    "배관": ["관로", "파이프", "수도관", "하수관", "오수관"],
    "막힘": ["폐색", "차단", "정체", "막히는 현상"],
    "역류": ["거꾸로 흐름", "백플로우", "물이 넘침", "토출"],
    "악취": ["불쾌한 냄새", "이취", "하수구 냄새", "썩은 내"],
    "고압세척": ["고압 청소", "워터젯 세척", "배관 스케일링", "초고압 세척"],
    "뚫": ["통수", "소통", "뚫어", "해결"],
    "스케일링": ["찌꺼기 제거", "관로 청소", "기름때 제거", "내부 스케일링"],
}

# ─── 유틸 ──────────────────────────────────────────────────────────────────────

def load_faqs() -> list[dict]:
    """faq6000.txt 파싱 → [{q, a}, ...] 목록 반환"""
    if not FAQ_FILE.exists():
        return []
    raw = FAQ_FILE.read_text(encoding="utf-8")
    items = []
    for chunk in raw.split("\n\n"):
        lines = chunk.split("\n")
        q_line = next((l for l in lines if l.lstrip().startswith("Q.")), None)
        a_line = next((l for l in lines if l.lstrip().startswith("A.")), None)
        if not q_line or not a_line:
            continue
        q = q_line.lstrip()[2:].strip()
        a = a_line.lstrip()[2:].strip().replace("]]", "")
        if q.endswith("질문") or a.startswith("대답") or len(q) < 10 or len(a) < 10:
            continue
        items.append({"q": q, "a": a})
    return items

_ALL_FAQS: list[dict] = []  # 최초 1회만 파싱

def pick_faqs(region: str, keyword: str, seed_val: int, count: int = None) -> list[dict]:
    """시드 기반으로 8~10개 FAQ를 선택하고 region/keyword 치환"""
    global _ALL_FAQS
    if not _ALL_FAQS:
        _ALL_FAQS = load_faqs()
    if not _ALL_FAQS:
        return []
    rng = random.Random(seed_val)
    n = count if count else rng.randint(8, 10)
    selected = rng.sample(_ALL_FAQS, min(n, len(_ALL_FAQS)))
    return [
        {
            "q": item["q"].replace('"region"', region).replace('"keywords"', keyword),
            "a": item["a"].replace('"region"', region).replace('"keywords"', keyword),
        }
        for item in selected
    ]

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
    if REGIONS_JSON.exists():
        with open(REGIONS_JSON, encoding="utf-8") as f:
            return json.load(f)
    return None

def build_region_blocks(df: pd.DataFrame, main_keyword: str, mid_kw_lines: list[str],
                        primary_idx: int | None = None) -> list[dict]:
    # primary_idx 미지정 + regions_data.json 존재 → JSON 우선 사용 (단일 페이지 모드)
    if primary_idx is None:
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

    if primary_idx is None:
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
    """이미지를 WebP로 변환·압축 (EXIF 제거, max_kb 이하)"""
    target = max_kb * 1024
    with Image.open(src) as img:
        img = img.convert("RGB")
        clean = Image.new("RGB", img.size)
        clean.putdata(list(img.getdata()))  # type: ignore[arg-type]
        w, h = clean.size
        clean = clean.crop((
            random.randint(1, 3), random.randint(1, 3),
            w - random.randint(1, 3), h - random.randint(1, 3),
        ))
        # WebP: quality 80→60→40 순으로 시도
        for quality in [80, 65, 50, 40, 30]:
            buf = BytesIO()
            clean.save(buf, format="WEBP", quality=quality, method=4)
            if buf.tell() <= target:
                dst.write_bytes(buf.getvalue())
                return
        max_dim = 1200
        if max(clean.size) > max_dim:
            clean.thumbnail((max_dim, max_dim), Image.LANCZOS)
        buf = BytesIO()
        clean.save(buf, format="WEBP", quality=30, method=4)
        dst.write_bytes(buf.getvalue())

def select_diverse_photos(n: int) -> list[Path]:
    exts = {".jpg", ".jpeg", ".png", ".webp"}
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
    img_dir.mkdir(parents=True, exist_ok=True)
    n = random.randint(*GALLERY_RANGE)
    photos = select_diverse_photos(n)
    paths: list[str] = []
    # SEO 파일명: 지역-키워드-작업사진-N.webp (공백→하이픈, 특수문자 제거)
    safe_region  = re.sub(r'[^\w가-힣]', '-', region).strip('-')
    safe_keyword = re.sub(r'[^\w가-힣]', '-', keyword).strip('-')
    for i, src in enumerate(photos):
        fname = f"{safe_region}-{safe_keyword}-작업사진-{i + 1}.webp"
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
    if dst_dir.exists():
        shutil.rmtree(dst_dir)
    dst_dir.mkdir(parents=True)
    exts = {".jpg", ".jpeg", ".png", ".webp", ".gif"}
    if not FIRST_IMG_DIR.exists():
        return []
    imgs = sorted(
        [p for p in FIRST_IMG_DIR.iterdir()
         if p.suffix.lower() in exts and p.stem[:2].isdigit()],
        key=lambda p: p.name,
    )
    paths = []
    for img in imgs:
        dst = dst_dir / img.name
        shutil.copy2(img, dst)
        paths.append(f"images/first/{img.name}")
    return paths

# ─── 후기 텍스트 처리 ─────────────────────────────────────────────────────────

def apply_synonyms_review(text: str) -> str:
    """후기 텍스트용 45% 확률 치환 함수"""
    for word, syns in SYNONYMS.items():
        if word in text and random.random() < 0.45:
            replacement = random.choice(syns)
            text = text.replace(word, replacement, random.randint(1, 2))
    return text

def process_review(region: str, keyword: str) -> list[str]:
    if not TEXT_DIR.exists():
        return ["후기 내용을 불러올 수 없습니다."]
        
    txt_files = list(TEXT_DIR.glob("*.txt"))
    if not txt_files:
        return ["후기 내용을 불러올 수 없습니다."]

    raw = (random.choice(txt_files)).read_text(encoding="utf-8")

    raw = re.sub(r"0\d{1,2}[-\s]?\d{3,4}[-\s]?\d{4}", "", raw)
    raw = re.sub(r"출장비\s*무료[^.。]*[.。]?", "", raw)

    paras = [p.strip() for p in raw.split("\n\n") if p.strip()]
    if len(paras) > 3:
        head, tail = paras[:1], paras[-1:]
        mid = paras[1:-1]
        random.shuffle(mid)
        paras = head + mid + tail

    # 동의어 치환
    paras = [apply_synonyms_review(p) for p in paras]

    # 임의의 문단에 지역+키워드 강제 주입
    inject_at = random.sample(range(len(paras)), min(3, len(paras)))
    for pos in inject_at:
        paras[pos] = f"{region} {keyword} – " + paras[pos]

    # 만약 원본 텍스트에 사용자가 직접 __REGION__ 과 __KW__ 를 적어두었다면 실제 값으로 교체
    result = []
    for p in paras:
        p = p.replace("__REGION__", region).replace("__KW__", keyword)
        result.append(p)

    return result

# ─── 단일 페이지 빌드 ─────────────────────────────────────────────────────────

def build_one(page_dir: Path, keywords: list[str], mid_kw_lines: list[str],
              df, env, tpl, first_images: list[str], page_num: int):
    page_dir.mkdir(parents=True, exist_ok=True)
    img_dir = page_dir / "images"

    main_keyword  = random.choice(keywords[:6])
    region_blocks = build_region_blocks(df, main_keyword, mid_kw_lines)
    primary_name  = region_blocks[0]["name"]

    rel_path      = page_dir.relative_to(OUTPUT_DIR)
    canonical_url = f"{SITE_DOMAIN}/{rel_path.as_posix()}/"
    first_img_name = Path(first_images[0]).name if first_images else ""
    og_image_url  = f"{SITE_DOMAIN}/images/first/{first_img_name}" if first_img_name else ""

    title_text = random.choice(TITLE_POOL).format(region=primary_name, keyword=main_keyword)

    # [수정] KeyError: 'region'을 방지하기 위해 region=primary_name 매개변수 반드시 포함
    desc_text  = random.choice(DESC_POOL).format(
        region=primary_name,
        keyword=main_keyword, 
        count=REGION_BLOCK_COUNT, 
        count_plus_3=REGION_BLOCK_COUNT + 3
    )

    gallery_images = process_gallery_named(img_dir, primary_name, main_keyword)
    main_gallery   = gallery_images[:3]
    sub_gallery    = [(p, p) for p in gallery_images[3:]]

    first_imgs_rel = [f"../images/first/{Path(p).name}" for p in first_images]

    review_paras = process_review(primary_name, main_keyword)
    faqs = pick_faqs(primary_name, main_keyword, seed_val=page_num)

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
        faqs            = faqs,
        google_apps_url = GOOGLE_APPS_URL,
        build_time      = datetime.now().strftime("%Y-%m-%d %H:%M"),
        block_count     = len(region_blocks),
        canonical_url              = canonical_url,
        og_image_url               = og_image_url,
        google_site_verification   = GOOGLE_SITE_VERIFICATION,
        naver_site_verification    = NAVER_SITE_VERIFICATION,
    )

    out = page_dir / "index.html"
    out.write_text(html, encoding="utf-8")
    print(f"  [page {page_num}] {primary_name} / {main_keyword}  gallery={len(gallery_images)}")
    return out

# ─── SEO 파일 생성 ──────────────────────────────────────────────────────────────

def write_robots_txt():
    content = f"User-agent: *\nAllow: /\nSitemap: {SITE_DOMAIN}/sitemap.xml\n"
    (OUTPUT_DIR / "robots.txt").write_text(content, encoding="utf-8")
    print("  [SEO] robots.txt 생성 완료")

def write_sitemap(urls: list[str]):
    today = datetime.now().strftime("%Y-%m-%d")
    lines = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">',
    ]
    for url in urls:
        lines.append(
            f'  <url><loc>{url}</loc><lastmod>{today}</lastmod>'
            f'<changefreq>weekly</changefreq><priority>0.8</priority></url>'
        )
    lines.append("</urlset>")
    (OUTPUT_DIR / "sitemap.xml").write_text("\n".join(lines), encoding="utf-8")
    print(f"  [SEO] sitemap.xml 생성 완료 ({len(urls)}개 URL)")

# ─── 메인 빌드 ────────────────────────────────────────────────────────────────

def build(test_count: int = 0):
    print("=" * 55)
    print("  build.py  -  Static Site Generator")
    if test_count:
        print(f"  [TEST MODE]  {test_count}개 페이지 생성")
    print("=" * 55)

    OUTPUT_DIR.mkdir(exist_ok=True)
    IMAGES_OUT_DIR.mkdir(exist_ok=True)

    print("[1/4] 데이터 로드 중...")
    keywords     = load_lines(KEYWORDS_FILE)
    mid_kw_lines = load_lines(MID_KW_FILE)
    df           = load_regions()

    print("[2/4] 상단 이미지 복사 중...")
    first_images = copy_first_images()

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
        generated = []
        canonical_urls = []
        for i in range(1, test_count + 1):
            page_dir = OUTPUT_DIR / f"test-{i}"
            out = build_one(page_dir, keywords, mid_kw_lines, df, env, tpl,
                            first_images, i)
            generated.append(out)
            canonical_urls.append(f"{SITE_DOMAIN}/test-{i}/")

        write_robots_txt()
        write_sitemap(canonical_urls)
        print("-" * 55)
        print(f"[DONE] {test_count}개 테스트 페이지 생성 완료")
        for p in generated:
            print(f"  -> {p}")
    else:
        main_keyword  = random.choice(keywords[:6])
        region_blocks = build_region_blocks(df, main_keyword, mid_kw_lines)
        primary_name   = region_blocks[0]["name"]

        canonical_url  = f"{SITE_DOMAIN}/"
        first_img_name = Path(first_images[0]).name if first_images else ""
        og_image_url   = f"{SITE_DOMAIN}/images/first/{first_img_name}" if first_img_name else ""

        title_text = random.choice(TITLE_POOL).format(
            region=primary_name, keyword=main_keyword
        )
        
        # [수정] KeyError 방지용 region=primary_name 파라미터 추가
        desc_text = random.choice(DESC_POOL).format(
            region=primary_name,
            keyword=main_keyword, 
            count=REGION_BLOCK_COUNT,
            count_plus_3=REGION_BLOCK_COUNT + 3
        )

        gallery_images = process_gallery_named(IMAGES_OUT_DIR, primary_name, main_keyword)
        main_gallery   = gallery_images[:3]
        sub_gallery    = [(p, p) for p in gallery_images[3:]]
        review_paras   = process_review(primary_name, main_keyword)
        faqs           = pick_faqs(primary_name, main_keyword, seed_val=0)

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
            faqs            = faqs,
            google_apps_url = GOOGLE_APPS_URL,
            build_time      = datetime.now().strftime("%Y-%m-%d %H:%M"),
            block_count     = len(region_blocks),
            canonical_url              = canonical_url,
            og_image_url               = og_image_url,
            google_site_verification   = GOOGLE_SITE_VERIFICATION,
            naver_site_verification    = NAVER_SITE_VERIFICATION,
        )

        out = OUTPUT_DIR / "index.html"
        out.write_text(html, encoding="utf-8")
        write_robots_txt()
        write_sitemap([canonical_url])
        print(f"[OK] {out}  ({primary_name} / {main_keyword})")
        print(f"     gallery={len(gallery_images)}")

# ─── 미리 굽기 (pages_bank/) ──────────────────────────────────────────────────

def build_bank(count: int):
    """모든 페이지를 pages_bank/에 미리 생성 (공유 이미지 풀 사용)"""
    BANK_DIR       = BASE_DIR / "pages_bank"
    BANK_IMG_DIR   = BANK_DIR / "images"
    BANK_FIRST_DIR = BANK_IMG_DIR / "first"
    BANK_GAL_DIR   = BANK_IMG_DIR / "gallery"

    print("=" * 55)
    print(f"  build_bank  -  {count}개 페이지 미리 굽기 (지역 기반)")
    print("=" * 55)

    # 이미지가 이미 있으면 재처리 생략, 기존 page-NNNN 폴더만 삭제
    regen_images = not BANK_GAL_DIR.exists() or not any(BANK_GAL_DIR.iterdir())
    if regen_images:
        if BANK_DIR.exists():
            shutil.rmtree(BANK_DIR)
        for d in [BANK_DIR, BANK_IMG_DIR, BANK_FIRST_DIR, BANK_GAL_DIR]:
            d.mkdir(parents=True)
    else:
        print("  (기존 이미지 풀 재사용)")
        for p in BANK_DIR.iterdir():
            if p.name != "images" and p.is_dir():
                shutil.rmtree(p)

    # 상단 이미지 복사 (숫자로 시작하는 파일만)
    exts = {".jpg", ".jpeg", ".png", ".webp", ".gif"}
    if regen_images and FIRST_IMG_DIR.exists():
        for p in sorted(FIRST_IMG_DIR.iterdir()):
            if p.suffix.lower() in exts and p.stem[:2].isdigit():
                shutil.copy2(p, BANK_FIRST_DIR / p.name)
    first_imgs_rel = [f"../images/first/{p.name}" for p in sorted(BANK_FIRST_DIR.iterdir()) if p.is_file()]
    first_img_name = Path(first_imgs_rel[0]).name if first_imgs_rel else ""

    # 갤러리 공유 풀 (이미지 없으면 새로 처리)
    if regen_images:
        print("[1/3] 공유 갤러리 이미지 처리 중...")
        photo_exts = {".jpg", ".jpeg", ".png", ".webp"}
        all_photos = sorted([p for p in PHOTOS_DIR.iterdir() if p.suffix.lower() in photo_exts]) if PHOTOS_DIR.exists() else []
        gallery_pool: list[str] = []
        for idx, src in enumerate(all_photos):
            fname = f"배관막힘-작업사진-{idx+1:03d}.webp"
            try:
                wash_and_compress(src, BANK_GAL_DIR / fname, max_kb=100)
                gallery_pool.append(f"../images/gallery/{fname}")
            except Exception as e:
                print(f"  [WARN] {src.name}: {e}")
        print(f"  공유 이미지: {len(gallery_pool)}개")
    else:
        gallery_pool = [f"../images/gallery/{p.name}" for p in sorted(BANK_GAL_DIR.iterdir()) if p.is_file()]
        print(f"[1/3] 기존 갤러리 풀 재사용: {len(gallery_pool)}개")

    # 데이터 로드 + 지역×키워드 조합 생성
    print("[2/3] 데이터 로드 및 조합 생성 중...")
    keywords     = load_lines(KEYWORDS_FILE)
    mid_kw_lines = load_lines(MID_KW_FILE)
    df           = load_regions()
    region_indices = df.index.tolist()

    # 1,095 지역 × 상위 6 키워드 = 최대 6,570 고유 조합
    combos = [(ri, kw) for kw in keywords[:6] for ri in region_indices]
    random.shuffle(combos)
    combos = combos[:count]
    print(f"  지역 수: {len(region_indices)}, 조합 수: {len(combos)}")

    # 1단계: 전체 페이지 메타데이터 사전 생성 (내부 링크용)
    print("  내부 링크 인덱스 생성 중...")
    page_meta = []
    for i, (ri, kw) in enumerate(combos, 1):
        primary_name = region_fullname(df.loc[ri])
        page_meta.append({"num": i, "url": f"/page-{i:04d}/", "keyword": kw, "region": primary_name})

    # 키워드별 페이지 목록 인덱스
    kw_index: dict[str, list] = {}
    for pm in page_meta:
        kw_index.setdefault(pm["keyword"], []).append(pm)

    env = Environment(loader=FileSystemLoader(str(BASE_DIR)), autoescape=False, keep_trailing_newline=True)
    env.filters["nl2br"] = lambda v: v.replace("\n", "<br>")
    tpl = env.get_template(TEMPLATE_FILE)

    # 2단계: 페이지 생성 (내부 링크 포함)
    print(f"[3/3] {count}개 페이지 생성 중...")
    for i, (region_idx, main_keyword) in enumerate(combos, 1):
        page_dir = BANK_DIR / f"page-{i:04d}"
        page_dir.mkdir(exist_ok=True)

        region_blocks = build_region_blocks(df, main_keyword, mid_kw_lines, primary_idx=region_idx)
        primary_name  = region_blocks[0]["name"]

        canonical_url = f"{SITE_DOMAIN}/page-{i:04d}/"
        og_image_url  = f"{SITE_DOMAIN}/images/first/{first_img_name}" if first_img_name else ""

        title_text = random.choice(TITLE_POOL).format(region=primary_name, keyword=main_keyword)
        desc_text  = random.choice(DESC_POOL).format(
            region=primary_name, keyword=main_keyword,
            count=REGION_BLOCK_COUNT, count_plus_3=REGION_BLOCK_COUNT + 3,
        )

        n_gal        = random.randint(*GALLERY_RANGE)
        selected     = random.sample(gallery_pool, min(n_gal, len(gallery_pool))) if gallery_pool else []
        main_gallery = selected[:3]
        sub_gallery  = [(p, p) for p in selected[3:]]

        # 같은 키워드 다른 지역 페이지 6개 (내부 링크)
        candidates  = [p for p in kw_index.get(main_keyword, []) if p["num"] != i]
        related_pages = random.sample(candidates, min(6, len(candidates)))

        html = tpl.render(
            phone=PHONE, site_name=SITE_NAME,
            region=primary_name, keyword=main_keyword,
            title_text=title_text, desc_text=desc_text,
            region_blocks=region_blocks,
            first_images=first_imgs_rel,
            main_gallery=main_gallery, sub_gallery=sub_gallery,
            review_paras=process_review(primary_name, main_keyword),
            faqs=pick_faqs(primary_name, main_keyword, seed_val=i),
            google_apps_url=GOOGLE_APPS_URL,
            build_time=datetime.now().strftime("%Y-%m-%d %H:%M"),
            block_count=len(region_blocks),
            canonical_url=canonical_url, og_image_url=og_image_url,
            google_site_verification=GOOGLE_SITE_VERIFICATION,
            naver_site_verification=NAVER_SITE_VERIFICATION,
            related_pages=related_pages,
        )
        (page_dir / "index.html").write_text(html, encoding="utf-8")
        if i % 100 == 0 or i == count:
            print(f"  [{i:>4}/{count}] {primary_name} / {main_keyword}")

    print("=" * 55)
    print(f"[완료] pages_bank/ 에 {count}개 페이지 생성됨")
    print(f"  공유 이미지 풀: {len(gallery_pool)}개")
    print("=" * 55)


if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == "bank":
        n = int(sys.argv[2]) if len(sys.argv) > 2 else 1000
        build_bank(n)
    else:
        count = int(sys.argv[1]) if len(sys.argv) > 1 else 0
        build(test_count=count)