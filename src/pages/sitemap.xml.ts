// src/pages/sitemap.xml.ts — 자동 sitemap.xml 생성
import type { APIRoute } from 'astro';
import { getAllRegions, SIDO_SLUG } from '../lib/regions';

const SITE = 'https://plumbers24.netlify.app';

export const GET: APIRoute = async () => {
  const allRegions = getAllRegions();
  const now = new Date().toISOString().slice(0, 10);

  // 정적 페이지
  const staticPages = ['/', '/about', '/contact', '/seoul', '/gyeonggi', '/reviews', '/sitemap-page'];

  // 시군구 페이지
  const sigungus = new Set<string>();
  allRegions.forEach(r => {
    const slug = SIDO_SLUG[r.sidoname];
    if (slug) sigungus.add(`/${slug}/${encodeURIComponent(r.sigungu)}`);
  });

  // 읍면동 페이지
  const dongs = allRegions
    .filter(r => r.dong)
    .map(r => {
      const slug = SIDO_SLUG[r.sidoname];
      if (!slug) return '';
      return `/${slug}/${encodeURIComponent(r.sigungu)}/${encodeURIComponent(r.dong)}`;
    })
    .filter(Boolean);

  const allUrls = [
    ...staticPages.map(p => ({ url: p, priority: '1.0', changefreq: 'weekly' })),
    ...['  /seoul', '/gyeonggi'].map(p => ({ url: p.trim(), priority: '0.9', changefreq: 'weekly' })),
    ...[...sigungus].map(u => ({ url: u, priority: '0.8', changefreq: 'weekly' })),
    ...dongs.map(u => ({ url: u, priority: '0.7', changefreq: 'monthly' })),
  ];

  const xml = `<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
${allUrls.map(({ url, priority, changefreq }) => `  <url>
    <loc>${SITE}${url}</loc>
    <lastmod>${now}</lastmod>
    <changefreq>${changefreq}</changefreq>
    <priority>${priority}</priority>
  </url>`).join('\n')}
</urlset>`;

  return new Response(xml, {
    headers: {
      'Content-Type': 'application/xml; charset=utf-8',
    },
  });
};
