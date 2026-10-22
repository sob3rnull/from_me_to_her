import type { NextConfig } from 'next';
const config: NextConfig = {
  async rewrites() {
    const backend = process.env.VAULT_API_URL || 'http://127.0.0.1:8000';
    if (!/^http:\/\/127\.0\.0\.1:(8000|8100)$/.test(backend)) throw new Error('Local backend required');
    return [{ source: '/api/:path*', destination: `${backend}/api/:path*` }];
  },
  async headers() {
    return [{ source: '/:path*', headers: [
      { key: 'Cache-Control', value: 'no-store' },
      { key: 'X-Content-Type-Options', value: 'nosniff' },
      { key: 'Referrer-Policy', value: 'no-referrer' },
      { key: 'X-Frame-Options', value: 'DENY' },
    ] }];
  },
};
export default config;
