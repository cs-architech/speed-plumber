// src/lib/regions.ts  — region.csv 파싱 유틸리티 (빌드 타임 전용)
import { readFileSync } from 'node:fs';
import { resolve } from 'node:path';

export interface RegionRow {
  sidoname: string;     // 서울특별시 | 경기도
  sigungu:  string;     // 강남구 | 화성
  dong:     string;     // 역삼동 | 동탄1동 (빈 문자열 가능)
  lat:      number;
  lon:      number;
}

let _cache: RegionRow[] | null = null;

function parseCSVLine(line: string): string[] {
  const result: string[] = [];
  let cur = '';
  let inQuote = false;
  for (let i = 0; i < line.length; i++) {
    const c = line[i];
    if (c === '"') { inQuote = !inQuote; continue; }
    if (c === ',' && !inQuote) { result.push(cur); cur = ''; continue; }
    cur += c;
  }
  result.push(cur);
  return result;
}

export function getAllRegions(): RegionRow[] {
  if (_cache) return _cache;
  const csvPath = resolve(process.cwd(), 'region.csv');
  const text = readFileSync(csvPath, 'utf-8').replace(/^﻿/, '');
  const rows: RegionRow[] = [];
  const lines = text.split('\n');
  for (let i = 1; i < lines.length; i++) {
    const line = lines[i].trim();
    if (!line) continue;
    const parts = parseCSVLine(line);
    if (parts.length < 6) continue;
    const sidoname = parts[1]?.trim() ?? '';
    const sigungu  = parts[2]?.trim() ?? '';
    const dong     = parts[3]?.trim() ?? '';
    const lat      = parseFloat(parts[4] ?? '0');
    const lon      = parseFloat(parts[5] ?? '0');
    if (!sidoname || !sigungu) continue;
    rows.push({ sidoname, sigungu, dong, lat, lon });
  }
  _cache = rows;
  return rows;
}

export function getByCity(sidoname: string): RegionRow[] {
  return getAllRegions().filter(r => r.sidoname === sidoname);
}

export function getUniqueSigungu(sidoname: string): string[] {
  return [...new Set(getByCity(sidoname).map(r => r.sigungu))].filter(Boolean);
}

export function getDongsBySigungu(sidoname: string, sigungu: string): RegionRow[] {
  return getByCity(sidoname).filter(r => r.sigungu === sigungu && r.dong);
}

export function getSigunguCentroid(sidoname: string, sigungu: string): { lat: number; lon: number } {
  const dongs = getDongsBySigungu(sidoname, sigungu);
  if (!dongs.length) {
    const hub = getByCity(sidoname).find(r => r.sigungu === sigungu);
    return { lat: hub?.lat ?? 37.5665, lon: hub?.lon ?? 126.978 };
  }
  const lat = dongs.reduce((s, r) => s + r.lat, 0) / dongs.length;
  const lon = dongs.reduce((s, r) => s + r.lon, 0) / dongs.length;
  return { lat, lon };
}

// 근접 지역 N개 반환 (같은 시도, 유클리드 거리 기준)
export function getNearbyDongs(
  sidoname: string, sigungu: string, dong: string,
  count = 10
): RegionRow[] {
  const target = getAllRegions().find(
    r => r.sidoname === sidoname && r.sigungu === sigungu && r.dong === dong
  );
  if (!target) return [];
  return getAllRegions()
    .filter(r => r.sidoname === sidoname && r.dong && !(r.sigungu === sigungu && r.dong === dong))
    .map(r => ({
      ...r,
      _dist: Math.hypot(r.lat - target.lat, r.lon - target.lon),
    }))
    .sort((a: any, b: any) => a._dist - b._dist)
    .slice(0, count);
}

export const SIDO_SLUG: Record<string, string> = {
  '서울특별시': 'seoul',
  '경기도': 'gyeonggi',
};

export const SLUG_SIDO: Record<string, string> = {
  'seoul': '서울특별시',
  'gyeonggi': '경기도',
};

// 지역 페이지 URL 생성
export function regionUrl(sidoname: string, sigungu?: string, dong?: string): string {
  const slug = SIDO_SLUG[sidoname] ?? sidoname;
  if (!sigungu) return `/${slug}`;
  const sgSlug = encodeURIComponent(sigungu);
  if (!dong) return `/${slug}/${sgSlug}`;
  return `/${slug}/${sgSlug}/${encodeURIComponent(dong)}`;
}

// 페이지 타이틀용 full label
export function regionLabel(sidoname: string, sigungu?: string, dong?: string): string {
  if (!sigungu) return sidoname;
  if (!dong) return `${sigungu}`;
  return `${sigungu} ${dong}`;
}
