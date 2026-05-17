// src/data/contents_list_fix_netlify.ts
// 배포·플랫폼 관련 설정. 이 파일만 수정하면 사이트 전체에 반영됩니다.

export const siteConfig = {
  // ── 기본 사이트 정보 ────────────────────────────────────────────────────────
  siteUrl:    'https://plumbers24.netlify.app',
  siteName:   '배관매니저',
  phone:      '1866-2449',
  tel:        'tel:18662449',
  copyright:  '© 2025 배관매니저',

  // ── Google Apps Script (폼 접수 + 방문자 카운터 공용) ────────────────────────
  appsScriptUrl: 'https://script.google.com/macros/s/AKfycbxPiUmBKUWRPdxvht5K9cLHFMJ83ML_S8qY0PzgeqnL9TfZs_IZJB4alpz0NUcRzv0/exec',

  // ── OG / SNS 기본 이미지 ─────────────────────────────────────────────────────
  ogImage:       '/og-default.jpg',
  ogImageWidth:  '1200',
  ogImageHeight: '630',

  // ── 지역 slug (빌드 라우팅용) ─────────────────────────────────────────────────
  sidoSlugs: {
    '서울특별시': 'seoul',
    '경기도':     'gyeonggi',
  } as Record<string, string>,

  // ── 서비스 지역 요약 (각 시도 페이지 헤드라인용) ───────────────────────────────
  seoulLabel:    '서울특별시',
  gyeonggiLabel: '경기도',

  // ── 네비게이션 메뉴 ───────────────────────────────────────────────────────────
  navLinks: [
    { label: '홈',       href: '/' },
    { label: '서울',     href: '/seoul' },
    { label: '경기',     href: '/gyeonggi' },
    { label: '배관후기', href: '/reviews' },
    { label: '상담신청', href: '/contact' },
  ],
} as const;
