  import adapter from '@sveltejs/adapter-static';
import { vitePreprocess } from '@sveltejs/vite-plugin-svelte';

/** @type {import('@sveltejs/kit').Config} */
const config = {
  // Consult https://kit.svelte.dev/docs/integrations#preprocessors
  // for more information about preprocessors
  preprocess: vitePreprocess(),

  kit: {
    // Use static adapter for serving from FastAPI
    adapter: adapter({
      pages: 'build',
      assets: 'build',
      fallback: 'index.html', // SPA fallback for client-side routing
      precompress: false
    }),
    alias: {
      $lib: './src/lib',
      $components: './src/components',
      $stores: './src/stores',
      $types: './src/types'
    },
    // Prerender specific routes for static hosting
    prerender: {
      entries: ['/', '/tenants', '/templates', '/licenses'],
      handleMissingId: 'warn'
    }
  }
};

export default config;
