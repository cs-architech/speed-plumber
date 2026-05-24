#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
patch_faq.py — pages_bank/ 기존 HTML에 FAQ 섹션 추가
이미 FAQ가 있는 파일은 건너뜀
"""

import random
import re
from pathlib import Path

BASE_DIR   = Path(__file__).parent
BANK_DIR   = BASE_DIR / "pages_bank"
FAQ_FILE   = BASE_DIR / "faq6000.txt"

# ── FAQ 데이터 로드 ─────────────────────────────────────────────────────────────
def load_faqs() -> list[dict]:
    if not FAQ_FILE.exists():
        print(f"[ERROR] {FAQ_FILE} 없음")
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

# ── 지역명 추출 (phone-header h1 기준) ──────────────────────────────────────────
def extract_region_keyword(html: str) -> tuple[str, str]:
    m = re.search(r'<h1[^>]*>([^<]+)</h1>', html)
    if m:
        text = m.group(1).strip()
        # "지역명 키워드 전문 업체 · ..." 패턴
        parts = text.split()
        if len(parts) >= 2:
            # 마지막 "전문" 앞까지에서 키워드 추출
            kw_pool = ['싱크대막힘', '변기막힘', '배관막힘', '하수구막힘',
                       '우수관막힘', '하수구역류', '배관고압세척', '하수구뚫음']
            for kw in kw_pool:
                if kw in text:
                    region = text[:text.index(kw)].strip()
                    return region, kw
            return " ".join(parts[:2]), parts[2] if len(parts) > 2 else "배관막힘"
    return "해당지역", "배관막힘"

# ── FAQ HTML 생성 ───────────────────────────────────────────────────────────────
FAQ_CSS = """
/* ── FAQ Accordion ── */
.faq-wrap{margin-top:8px}
.faq-title{font-size:1.15rem;font-weight:800;color:#1a237e;margin-bottom:4px;display:flex;align-items:center;gap:8px}
.faq-sub{font-size:.82rem;color:#888;margin-bottom:14px}
.faq-item{border:1px solid #e0e0e0;border-radius:12px;overflow:hidden;margin-bottom:8px;transition:box-shadow .2s}
.faq-item:hover{box-shadow:0 2px 10px rgba(26,35,126,.1)}
.faq-btn{width:100%;text-align:left;display:flex;align-items:flex-start;justify-content:space-between;gap:10px;padding:14px 16px;background:#fff;border:none;cursor:pointer;font-family:inherit;font-size:.9rem;font-weight:700;color:#222;line-height:1.55}
.faq-btn:hover{background:#f0f3ff}
.faq-q-label{color:#1a237e;font-weight:900;margin-right:6px;font-size:.95rem}
.faq-arrow{flex-shrink:0;font-size:.8rem;color:#aaa;transition:transform .3s;margin-top:2px}
.faq-answer{max-height:0;overflow:hidden;transition:max-height .35s ease}
.faq-answer-inner{padding:12px 16px 16px;background:#f0f3ff;border-top:1px solid #e3e8ff;font-size:.88rem;color:#444;line-height:1.8}
.faq-a-label{color:#ff6f00;font-weight:900;margin-right:6px}
@media(max-width:600px){.faq-btn{font-size:.85rem;padding:12px 14px}}"""

FAQ_JS = """
/* ── FAQ 아코디언 ── */
document.querySelectorAll('.faq-btn').forEach(function(btn) {
  btn.addEventListener('click', function() {
    var answer = this.nextElementSibling;
    var arrow  = this.querySelector('.faq-arrow');
    var isOpen = this.getAttribute('aria-expanded') === 'true';
    document.querySelectorAll('.faq-btn').forEach(function(b) {
      b.setAttribute('aria-expanded', 'false');
      b.nextElementSibling.style.maxHeight = '0';
      var a = b.querySelector('.faq-arrow'); if (a) a.style.transform = '';
    });
    if (!isOpen) {
      this.setAttribute('aria-expanded', 'true');
      answer.style.maxHeight = '800px';
      if (arrow) arrow.style.transform = 'rotate(180deg)';
    }
  });
});"""

def build_faq_html(region: str, keyword: str, faqs: list[dict]) -> str:
    items_html = ""
    for faq in faqs:
        q = faq["q"].replace("<", "&lt;").replace(">", "&gt;")
        a = faq["a"].replace("<", "&lt;").replace(">", "&gt;")
        items_html += f"""
      <div class="faq-item">
        <button type="button" class="faq-btn" aria-expanded="false">
          <span><span class="faq-q-label">Q.</span>{q}</span>
          <span class="faq-arrow">&#9660;</span>
        </button>
        <div class="faq-answer" style="max-height:0">
          <div class="faq-answer-inner"><span class="faq-a-label">A.</span>{a}</div>
        </div>
      </div>"""

    return f"""
<!-- ⑦ FAQ 자주 묻는 질문 -->
  <div class="section">
    <div class="faq-wrap">
      <div class="faq-title">&#128172; {region} {keyword} 자주 묻는 질문</div>
      <div class="faq-sub">{region} 배관막힘 관련 고객 FAQ</div>{items_html}
    </div>
  </div><!-- /section -->
"""

# ── 패치 실행 ───────────────────────────────────────────────────────────────────
def patch_file(html_path: Path, all_faqs: list[dict], seed: int) -> bool:
    html = html_path.read_text(encoding="utf-8")

    # 이미 FAQ 패치됐으면 건너뜀
    if "faq-wrap" in html or "faq-item" in html:
        return False

    region, keyword = extract_region_keyword(html)
    rng = random.Random(seed)
    n = rng.randint(8, 10)
    selected = rng.sample(all_faqs, min(n, len(all_faqs)))
    faqs = [
        {
            "q": f["q"].replace('"region"', region).replace('"keywords"', keyword),
            "a": f["a"].replace('"region"', region).replace('"keywords"', keyword),
        }
        for f in selected
    ]

    # 1) CSS 삽입 (</style> 바로 앞)
    if FAQ_CSS.strip()[:20] not in html:
        html = html.replace("</style>", FAQ_CSS + "\n</style>", 1)

    # 2) HTML 삽입 (</div><!-- /container --> 바로 앞)
    faq_html = build_faq_html(region, keyword, faqs)
    html = html.replace("\n</div><!-- /container -->", faq_html + "\n</div><!-- /container -->", 1)

    # 3) JS 삽입 (</script> 바로 앞)
    if "querySelectorAll('.faq-btn')" not in html:
        html = html.replace("</script>", FAQ_JS + "\n</script>", 1)

    html_path.write_text(html, encoding="utf-8")
    return True


def main():
    print("=" * 55)
    print("  patch_faq.py  —  기존 pages_bank/ HTML에 FAQ 주입")
    print("=" * 55)

    all_faqs = load_faqs()
    if not all_faqs:
        print("[ERROR] FAQ 데이터 없음")
        return

    print(f"[INFO] FAQ 항목 수: {len(all_faqs)}개")

    html_files = sorted(BANK_DIR.rglob("index.html"))
    total = len(html_files)
    print(f"[INFO] 대상 파일: {total}개\n")

    patched = 0
    skipped = 0
    for i, path in enumerate(html_files, 1):
        # 폴더명에서 시드 추출 (page-0001 → 1)
        folder = path.parent.name
        m = re.search(r'\d+', folder)
        seed = int(m.group()) if m else i

        result = patch_file(path, all_faqs, seed)
        if result:
            patched += 1
        else:
            skipped += 1

        if i % 200 == 0 or i == total:
            print(f"  [{i:>5}/{total}] 완료 {patched}개 / 스킵 {skipped}개")

    print("=" * 55)
    print(f"[완료] FAQ 주입: {patched}개 | 이미 있어서 스킵: {skipped}개")
    print("=" * 55)


if __name__ == "__main__":
    main()
