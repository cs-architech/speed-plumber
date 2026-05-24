// netlify/edge-functions/geo-blocker.ts
// KR-only geo-block + marketing scraper bot block

const BLOCKED_BOTS = ['AhrefsBot', 'SemrushBot', 'MJ12bot', 'PetalBot', 'DotBot', 'BLEXBot', 'MegaIndex', 'serpstatbot'];
const ALLOWED_BOTS = ['Googlebot', 'Google-Site-Verification', 'Google-InspectionTool', 'APIs-Google', 'AdsBot-Google', 'bingbot', 'Yeti', 'NaverBot', 'facebookexternalhit', 'Twitterbot', 'LinkedInBot', 'Slackbot', 'DuckDuckBot'];
const STATIC_PREFIX = ['/_astro/', '/images/', '/_assets/'];
const STATIC_EXT    = new Set(['.ico', '.png', '.jpg', '.jpeg', '.gif', '.svg', '.webp', '.css', '.js', '.woff', '.woff2', '.ttf', '.xml', '.txt']);

export default async function handler(request: Request, context: any) {
  const url = new URL(request.url);
  const path = url.pathname;

  // Always pass static assets through
  if (STATIC_PREFIX.some(p => path.startsWith(p))) return context.next();
  const dotIdx = path.lastIndexOf('.');
  if (dotIdx !== -1 && STATIC_EXT.has(path.slice(dotIdx))) return context.next();

  const ua = request.headers.get('user-agent') ?? '';

  // Block marketing/scraper bots
  if (BLOCKED_BOTS.some(bot => ua.includes(bot))) {
    return new Response('Forbidden', { status: 403 });
  }

  // Allow legitimate crawlers regardless of country
  if (ALLOWED_BOTS.some(bot => ua.toLowerCase().includes(bot.toLowerCase()))) {
    return context.next();
  }

  // Geo-block: KR only (undefined country = allow, avoids blocking during local dev)
  const country: string | undefined = context.geo?.country?.code;
  if (country && country !== 'KR') {
    return new Response('서비스 지역이 아닙니다 (KR only)', {
      status: 403,
      headers: { 'Content-Type': 'text/plain; charset=utf-8' },
    });
  }

  return context.next();
}

export const config = { path: '/*' };
