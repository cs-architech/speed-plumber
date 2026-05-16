// astro.config.mjs
import { defineConfig } from 'astro/config';
import tailwind from '@astrojs/tailwind';

export default defineConfig({
  site: 'https://plumbers24.netlify.app',
  integrations: [
    tailwind(),
  ],
  output: 'static',
  build: {
    assets: '_assets',
  },
});
