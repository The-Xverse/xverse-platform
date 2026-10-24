import { defineConfig } from 'astro/config';
import starlight from '@astrojs/starlight';
import { unified } from '@astrojs/markdown-remark';
import remarkBase from './scripts/remark-base.mjs';

const base = process.env.BASE_PATH || '/xverse-platform/';
const site = process.env.SITE_URL || 'https://the-xverse.github.io';
if (!base.startsWith('/') || !base.endsWith('/') || base.includes('..') || /[?#\\]/.test(base)) {
  throw new Error('BASE_PATH must be an absolute path ending in /, without traversal, query, or fragment.');
}
if (new URL(site).pathname !== '/' || !/^https?:$/.test(new URL(site).protocol)) {
  throw new Error('SITE_URL must be an HTTP(S) origin.');
}

export default defineConfig({
  site,
  base,
  trailingSlash: 'always',
  markdown: { processor: unified({ remarkPlugins: [[remarkBase, { base }]] }) },
  integrations: [starlight({
    title: 'X-Verse',
    description: 'Describe cyber-physical systems. Connect their realizations. Understand the evidence.',
    logo: { src: './src/assets/mark.svg', replacesTitle: false },
    favicon: '/favicon.svg',
    social: [{ icon: 'github', label: 'GitHub', href: 'https://github.com/The-Xverse/xverse-platform' }],
    customCss: ['./src/styles/docs.css'],
    editLink: { baseUrl: 'https://github.com/The-Xverse/xverse-platform/edit/main/website/' },
    pagefind: false,
    sidebar: [
      { label: 'Start here', items: [
        { label: 'Overview', slug: 'docs' },
        { label: 'Installation', slug: 'docs/getting-started/installation' },
        { label: 'Your first system', slug: 'docs/getting-started/first-system' },
        { label: 'Status & roadmap', slug: 'docs/status' },
      ] },
      { label: 'Concepts', items: [{ autogenerate: { directory: 'docs/concepts' } }] },
      { label: 'Guides', items: [{ autogenerate: { directory: 'docs/guides' } }] },
      { label: 'Reference', items: [
        { label: 'Reference overview', slug: 'docs/reference' },
        { label: 'Command line', slug: 'docs/reference/generated/cli' },
        { label: 'XDL schemas', items: [{ autogenerate: { directory: 'docs/reference/generated/schemas' } }] },
        { label: 'Profile schemas', items: [{ autogenerate: { directory: 'docs/reference/generated/profiles' } }] },
        { label: 'Source examples', slug: 'docs/reference/generated/examples' },
        { label: 'Python API ↗', link: '/reference/python/' },
        { label: 'C++ API ↗', link: '/reference/cpp/' },
      ] },
      { label: 'Development', items: [{ autogenerate: { directory: 'docs/development' } }] },
    ],
    components: { Search: './src/components/Search.astro' },
  })],
});
