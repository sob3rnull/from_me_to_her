import type { NextConfig } from 'next';
// trailingSlash emits /notes/index.html so any plain static file server (Caddy included) resolves routes.
const config: NextConfig = { output: 'export', trailingSlash: true };
export default config;
