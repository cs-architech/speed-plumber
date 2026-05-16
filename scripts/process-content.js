#!/usr/bin/env node
/**
 * scripts/process-content.js
 * ─────────────────────────────────────────────────────────────────
 * 빌드 전 자동 실행:
 *   '01. content upload/' 폴더에서 .txt 파일을 하루 최대 3개 읽어
 *   src/content/reviews/*.md 로 변환 후 원본을 '업로드완료/' 로 이동.
 *
 * 실행: node scripts/process-content.js
 * ─────────────────────────────────────────────────────────────────
 */

import fs   from 'fs';
import path from 'path';

const BASE        = new URL('..', import.meta.url).pathname.replace(/^\/([A-Za-z]:)/, '$1');
const UPLOAD_DIR  = path.join(BASE, '01. content upload');
const DONE_DIR    = path.join(UPLOAD_DIR, '업로드완료');
const REVIEWS_DIR = path.join(BASE, 'src', 'content', 'reviews');
const MAX_PER_RUN = 3;

// ── 키워드 치환 패턴 ─────────────────────────────────────────────────────────
const REGION_PATTERNS = [
  /안산|수원|군포|시흥|안양|의왕|광명|부천|화성|오산|인천|성남|종로구|중구|고양/g,
];
const KW_PATTERNS = [
  /하수구막힘|배관막힘|싱크대막힘|변기막힘|하수구역류|배관고압세척|하수구뚫음|배관뚫음/g,
];

// 동의어 치환 테이블
const SYNONYMS = {
  '해결': ['처리', '완료', '조치'],
  '전문가': ['기술자', '전문 기사', '숙련 기사'],
  '신속': ['빠르게', '즉시', '즉각'],
  '작업': ['시공', '조치', '서비스'],
  '막힘': ['폐색', '정체', '차단'],
  '역류': ['거꾸로 흐름', '백플로우'],
  '뚫': ['통수', '소통'],
};

function applySynonyms(text) {
  for (const [word, syns] of Object.entries(SYNONYMS)) {
    const re = new RegExp(word, 'g');
    let count = 0;
    text = text.replace(re, (m) => {
      count++;
      // 첫 번째 등장만 치환 (나머지 원문 유지)
      return count === 1 ? syns[Math.floor(Math.random() * syns.length)] : m;
    });
  }
  return text;
}

function slugify(str) {
  return str
    .replace(/[^\w\s가-힣]/g, '')
    .replace(/\s+/g, '-')
    .slice(0, 60)
    .toLowerCase();
}

function extractMeta(filename) {
  // 파일명 예: "1. 안산 하수구막힘, 꽉 막힌 속 시원하게.txt"
  const base    = path.basename(filename, '.txt');
  const region  = (base.match(/안산|수원|군포|시흥|안양|의왕|광명|부천|화성|오산|인천|성남/) || [''])[0];
  const keyword = (base.match(/하수구막힘|배관막힘|싱크대막힘|변기막힘|하수구역류/) || ['배관막힘'])[0];
  const title   = base.replace(/^\d+\.\s*/, '').trim();
  return { region, keyword, title };
}

function processText(raw, region, keyword) {
  // 전화번호 제거
  let text = raw.replace(/0\d{1,2}[-\s]?\d{3,4}[-\s]?\d{4}/g, '');
  // 지역명 → region, 키워드 → keyword
  for (const re of REGION_PATTERNS) text = text.replace(re, region || '지역');
  for (const re of KW_PATTERNS)     text = text.replace(re, keyword || '배관막힘');

  // 문단 셔플 (앞뒤 고정)
  const paras = text.split(/\n\n+/).map(p => p.trim()).filter(Boolean);
  if (paras.length > 3) {
    const [head, ...rest] = paras;
    const tail = rest.pop();
    const mid  = rest.sort(() => Math.random() - 0.5);
    text = [head, ...mid, tail].join('\n\n');
  }

  // 동의어 치환
  text = applySynonyms(text);
  return text;
}

// ── 메인 ────────────────────────────────────────────────────────────────────

function run() {
  // 필요 폴더 생성
  [DONE_DIR, REVIEWS_DIR].forEach(d => fs.mkdirSync(d, { recursive: true }));

  // 처리 대상 .txt 파일 수집 (업로드완료 제외)
  const all = fs.readdirSync(UPLOAD_DIR)
    .filter(f => f.endsWith('.txt'))
    .sort();

  if (all.length === 0) {
    console.log('[process-content] 처리할 파일 없음. 건너뜀.');
    return;
  }

  const targets = all.slice(0, MAX_PER_RUN);
  console.log(`[process-content] ${targets.length}개 파일 처리 시작 (전체 대기: ${all.length}개)`);

  for (const filename of targets) {
    const src  = path.join(UPLOAD_DIR, filename);
    const { region, keyword, title } = extractMeta(filename);

    let raw;
    try {
      raw = fs.readFileSync(src, 'utf-8');
    } catch (e) {
      console.warn(`  [SKIP] 읽기 실패: ${filename}`);
      continue;
    }

    const body = processText(raw, region, keyword);
    const date = new Date().toISOString().slice(0, 10);
    const slug = `${date}-${slugify(title)}`.slice(0, 80);

    const frontmatter = [
      '---',
      `title: "${title.replace(/"/g, "'")}"`,
      `date: "${date}"`,
      `slug: "${slug}"`,
      `region: "${region}"`,
      `keyword: "${keyword}"`,
      `image: ""`,
      '---',
      '',
    ].join('\n');

    const mdPath = path.join(REVIEWS_DIR, `${slug}.md`);
    fs.writeFileSync(mdPath, frontmatter + body, 'utf-8');

    // 원본 → 업로드완료/ 이동
    const dst = path.join(DONE_DIR, filename);
    fs.renameSync(src, dst);

    console.log(`  [OK] ${filename}`);
    console.log(`       → ${path.relative(BASE, mdPath)}`);
  }

  console.log('[process-content] 완료.');
}

run();
