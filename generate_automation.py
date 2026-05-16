# generate_automation.py
# 경로: d:\홈페이지제작\generate_automation.py
# 실행: python generate_automation.py
# 기능: 대량 SEO 페이지 메타데이터 생성 → src/data/db.json 저장

import os
import sys
import json
import csv
import math
import random
import shutil
import hashlib
import datetime
from pathlib import Path

# ─────────────────────────────────────────────
# 경로 상수
# ─────────────────────────────────────────────
BASE_DIR        = Path(__file__).parent
REGION_CSV      = BASE_DIR / "region.csv"
KEYWORDS_TXT    = BASE_DIR / "keywords.txt"
MID_KEYWORDS    = BASE_DIR / "mid-keywords.txt"
UPLOAD_CONTENT  = BASE_DIR / "01. content upload"
UPLOAD_TEXT     = BASE_DIR / "02. 업로드 텍스트"
UPLOAD_PHOTO    = BASE_DIR / "03. 업로드 사진"
PUBLISHED_DIR   = BASE_DIR / "content_published"
REVIEWS_DIR     = BASE_DIR / "src" / "content" / "reviews"
WASHED_DIR      = BASE_DIR / "public" / "images" / "washed"
DATA_DIR        = BASE_DIR / "src" / "data"
DB_PATH         = DATA_DIR / "db.json"

# 필요 디렉토리 보장
for d in [PUBLISHED_DIR, REVIEWS_DIR, WASHED_DIR, DATA_DIR]:
    d.mkdir(parents=True, exist_ok=True)

# ─────────────────────────────────────────────
# 1. CSV / TXT 로드
# ─────────────────────────────────────────────
def load_regions():
    """region.csv → [{시군구, 읍면동, lat, lon, region}, ...]"""
    regions = []
    with open(REGION_CSV, encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        for row in reader:
            sigungu = row.get("시군구", "").strip()
            eupmyeondong = row.get("읍면동", "").strip()
            try:
                lat = float(row.get("위도", 0) or 0)
                lon = float(row.get("경도", 0) or 0)
            except ValueError:
                lat, lon = 0.0, 0.0
            if not sigungu:
                continue
            region_name = f"{sigungu} {eupmyeondong}".strip() if eupmyeondong else sigungu
            regions.append({
                "sigungu": sigungu,
                "eupmyeondong": eupmyeondong,
                "region": region_name,
                "lat": lat,
                "lon": lon,
            })
    return regions


def load_keywords(path):
    """한 줄에 하나씩 키워드 로드, 빈 줄 제외"""
    with open(path, encoding="utf-8-sig") as f:
        return [line.strip() for line in f if line.strip()]


def load_mid_keywords():
    """mid-keywords.txt → 한 줄이 "/" 구분 문자열"""
    lines = load_keywords(MID_KEYWORDS)
    return lines  # 리스트 그대로 반환 (각 행 = 하나의 슬롯)


# ─────────────────────────────────────────────
# 2. Haversine 거리 계산 & 주변 지역
# ─────────────────────────────────────────────
def haversine(lat1, lon1, lat2, lon2):
    R = 6371.0
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlam = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlam / 2) ** 2
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


def build_nearby(regions, target_idx, top_n=5):
    """target 지역과 가장 가까운 top_n개 지역 반환"""
    t = regions[target_idx]
    if t["lat"] == 0 and t["lon"] == 0:
        return []
    distances = []
    for i, r in enumerate(regions):
        if i == target_idx:
            continue
        if r["lat"] == 0 and r["lon"] == 0:
            continue
        d = haversine(t["lat"], t["lon"], r["lat"], r["lon"])
        distances.append((d, r))
    distances.sort(key=lambda x: x[0])
    return [r for _, r in distances[:top_n]]


# ─────────────────────────────────────────────
# 3. 텍스트 리라이팅 (유사문서 회피)
# ─────────────────────────────────────────────
ENDER_MAP = {
    "입니다": ["이에요", "이랍니다", "이죠"],
    "합니다": ["해요", "한답니다", "하죠"],
    "됩니다": ["돼요", "된답니다", "되죠"],
    "있습니다": ["있어요", "있답니다", "있죠"],
    "습니다": ["어요", "답니다"],
}

def rewrite_text(text: str, seed: int) -> str:
    """문단 순서를 섞고 어미를 미세하게 변형하여 유사문서 회피"""
    rng = random.Random(seed)
    paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]
    rng.shuffle(paragraphs)

    result = []
    for para in paragraphs:
        for orig, variants in ENDER_MAP.items():
            if orig in para:
                choice = rng.choice(variants)
                para = para.replace(orig, choice, 1)  # 첫 번째 등장만 교체
        result.append(para)
    return "\n\n".join(result)


# ─────────────────────────────────────────────
# 4. 텍스트 파일 할당 및 이동
# ─────────────────────────────────────────────
def get_text_files():
    return sorted(UPLOAD_TEXT.glob("*.txt"))


def assign_text(pages: list, text_files: list):
    """페이지마다 텍스트 파일을 순환 할당하고, 사용된 파일은 published로 이동"""
    if not text_files:
        for p in pages:
            p["body_text"] = ""
            p["body_title"] = "업체 작업 후기"
        return

    used = set()
    file_contents = {}
    for tf in text_files:
        try:
            file_contents[tf] = tf.read_text(encoding="utf-8-sig")
        except Exception:
            file_contents[tf] = ""

    for i, page in enumerate(pages):
        tf = text_files[i % len(text_files)]
        raw = file_contents[tf]
        seed = hash(page["id"]) & 0xFFFFFF
        page["body_text"] = rewrite_text(raw, seed)
        # 제목: 첫 줄 또는 파일명
        first_line = raw.split("\n")[0].strip()
        page["body_title"] = first_line if first_line else tf.stem
        used.add(tf)

    # 사용된 파일 published로 이동
    for tf in used:
        dest = PUBLISHED_DIR / tf.name
        # 덮어쓰기 방지: 동일 파일명 있으면 타임스탬프 추가
        if dest.exists():
            dest = PUBLISHED_DIR / f"{tf.stem}_{datetime.datetime.now().strftime('%H%M%S')}{tf.suffix}"
        shutil.move(str(tf), str(dest))
    print(f"  텍스트 파일 {len(used)}개 published로 이동")


# ─────────────────────────────────────────────
# 5. 이미지 세탁 (EXIF 삭제, 사이즈 미세 조정)
# ─────────────────────────────────────────────
def wash_images(photo_files: list, page_id: str, seed: int) -> list:
    """이미지 세탁 후 washed 폴더에 저장, 파일명 리스트 반환"""
    try:
        from PIL import Image
    except ImportError:
        print("  [경고] Pillow 미설치 → pip install pillow")
        return []

    if not photo_files:
        return []

    rng = random.Random(seed)
    max_count = min(15, len(photo_files))
    min_count = min(5, max_count)
    count = rng.randint(min_count, max_count)
    selected = rng.sample(photo_files, count)

    result_names = []
    for src_path in selected:
        try:
            img = Image.open(src_path)
            # EXIF 삭제: 이미지를 새로 생성
            data = list(img.getdata())
            clean_img = Image.new(img.mode, img.size)
            clean_img.putdata(data)

            # 사이즈 미세 조정 (±2px)
            w, h = clean_img.size
            dw = rng.randint(-2, 2)
            dh = rng.randint(-2, 2)
            new_w = max(100, w + dw)
            new_h = max(100, h + dh)
            if dw != 0 or dh != 0:
                clean_img = clean_img.resize((new_w, new_h), Image.LANCZOS)

            # 품질 미세 조정 (92~97)
            quality = rng.randint(92, 97)
            ext = src_path.suffix.lower()
            safe_id = page_id.replace("/", "_").replace("\\", "_")
            out_name = f"{safe_id}_{src_path.stem}_w{ext}"
            out_path = WASHED_DIR / out_name

            save_kwargs = {"optimize": True}
            if ext in (".jpg", ".jpeg"):
                save_kwargs["quality"] = quality
            clean_img.save(out_path, **save_kwargs)
            result_names.append(f"/images/washed/{out_name}")
        except Exception as e:
            print(f"  [이미지 오류] {src_path.name}: {e}")
    return result_names


# ─────────────────────────────────────────────
# 6. 리뷰 파일 스케줄링 (하루 3개씩 마크다운 변환)
# ─────────────────────────────────────────────
def schedule_reviews():
    """01. content upload → src/content/reviews/*.md (하루 3개씩)"""
    content_files = sorted(UPLOAD_CONTENT.glob("*"))
    content_files = [f for f in content_files if f.is_file()]
    if not content_files:
        print("  리뷰 파일 없음 (01. content upload 폴더 비어있음)")
        return

    today = datetime.date.today()
    batch_size = 3

    for i, src in enumerate(content_files[:batch_size]):
        pub_date = today + datetime.timedelta(days=i // batch_size)
        slug = f"{pub_date.strftime('%Y%m%d')}_{i:03d}_{src.stem}"
        md_path = REVIEWS_DIR / f"{slug}.md"

        try:
            raw = src.read_text(encoding="utf-8-sig")
        except Exception:
            raw = src.read_text(encoding="cp949", errors="replace")

        lines = raw.strip().split("\n")
        title = lines[0].strip() if lines else src.stem
        body = "\n".join(lines[1:]).strip() if len(lines) > 1 else raw

        frontmatter = f"""---
title: "{title}"
date: "{pub_date.isoformat()}"
slug: "{slug}"
---

{body}
"""
        md_path.write_text(frontmatter, encoding="utf-8")
        dest = PUBLISHED_DIR / src.name
        if dest.exists():
            dest = PUBLISHED_DIR / f"{src.stem}_{datetime.datetime.now().strftime('%H%M%S')}{src.suffix}"
        shutil.move(str(src), str(dest))

    print(f"  리뷰 {min(batch_size, len(content_files))}개 마크다운 변환 완료")


# ─────────────────────────────────────────────
# 7. 메인 실행
# ─────────────────────────────────────────────
def main():
    print("=== 배관매니저 대량 페이지 생성 시작 ===\n")

    # 데이터 로드
    print("[1] 데이터 로드 중...")
    regions = load_regions()
    keywords = load_keywords(KEYWORDS_TXT)
    mid_kws = load_mid_keywords()

    # ── 테스트 모드: 첫 번째 지역 1개 + 첫 번째 키워드 1개 + 사진 15장만 처리 ──
    TEST_MODE = True  # 본 운영 시 False로 변경
    if TEST_MODE:
        regions      = regions[:1]
        keywords     = keywords[:1]
    # ── 테스트 모드 끝 ──

    print(f"  지역: {len(regions)}개 / 키워드: {len(keywords)}개 / 미드키워드: {len(mid_kws)}개")

    # 이미지 파일 목록
    photo_extensions = {".jpg", ".jpeg", ".png", ".webp"}
    photo_files = [
        f for f in UPLOAD_PHOTO.iterdir()
        if f.is_file() and f.suffix.lower() in photo_extensions
    ]
    print(f"  사진 파일: {len(photo_files)}개")

    # 텍스트 파일 목록
    text_files = get_text_files()
    print(f"  텍스트 파일: {len(text_files)}개")

    # 조합 생성
    print("\n[2] 페이지 메타데이터 생성 중...")
    pages = []
    for r_idx, region_data in enumerate(regions):
        nearby = build_nearby(regions, r_idx, top_n=5)
        for k_idx, keyword in enumerate(keywords):
            page_id = f"{region_data['sigungu']}-{region_data['eupmyeondong']}-{keyword}".replace(" ", "_")
            # ID 고유화를 위해 해시 suffix 추가
            hash_suffix = hashlib.md5(page_id.encode()).hexdigest()[:6]
            page_id = f"{hash_suffix}-{r_idx:04d}-{k_idx:02d}"

            seed = int(hashlib.md5(page_id.encode()).hexdigest(), 16) % (2**31)
            mid_kw = mid_kws[(r_idx * len(keywords) + k_idx) % len(mid_kws)] if mid_kws else ""

            page = {
                "id": page_id,
                "region": region_data["region"],
                "sigungu": region_data["sigungu"],
                "eupmyeondong": region_data["eupmyeondong"],
                "keyword": keyword,
                "lat": region_data["lat"],
                "lon": region_data["lon"],
                "mid_keyword": mid_kw,
                "nearby_areas": [
                    {
                        "region": n["region"],
                        "lat": n["lat"],
                        "lon": n["lon"],
                    }
                    for n in nearby
                ],
                "images": [],
                "body_text": "",
                "body_title": "",
            }
            pages.append(page)

    print(f"  총 {len(pages)}개 페이지 생성됨")

    # 텍스트 할당
    print("\n[3] 텍스트 파일 할당 중...")
    assign_text(pages, text_files)

    # 이미지 세탁 및 할당
    print("\n[4] 이미지 세탁 및 할당 중...")
    if photo_files:
        # 테스트 모드: 사진 최대 15장만 세탁
        pool_files = photo_files[:15] if TEST_MODE else photo_files
        print(f"  사진 {len(pool_files)}장 세탁 중... (전체 {len(photo_files)}장 중)")
        washed_pool = []
        rng = random.Random(42)
        for pf in pool_files:
            seed = rng.randint(0, 2**31)
            washed = wash_images([pf], f"pool_{pf.stem}", seed)
            washed_pool.extend(washed)

        # 페이지마다 5~15장 배분
        page_rng = random.Random(99)
        for page in pages:
            if not washed_pool:
                break
            count = page_rng.randint(5, min(15, len(washed_pool)))
            page["images"] = page_rng.sample(washed_pool, count)
        print(f"  세탁된 이미지 풀: {len(washed_pool)}장")
    else:
        print("  사진 파일 없음 → 이미지 할당 건너뜀")

    # 리뷰 스케줄링
    print("\n[5] 리뷰 파일 스케줄링 중...")
    schedule_reviews()

    # DB 저장
    print("\n[6] db.json 저장 중...")
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(DB_PATH, "w", encoding="utf-8") as f:
        json.dump(pages, f, ensure_ascii=False, indent=2)
    size_kb = DB_PATH.stat().st_size / 1024
    print(f"  저장 완료: {DB_PATH} ({size_kb:.1f} KB)")

    print(f"\n=== 완료! 총 {len(pages)}개 페이지 데이터 생성 ===")
    print(f"  다음 단계: astro build 또는 astro dev")


if __name__ == "__main__":
    main()
