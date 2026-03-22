import path from 'path';
import type { NextConfig } from 'next';

const configuredApiUrl = process.env.NEXT_PUBLIC_API_URL?.trim();

const nextConfig: NextConfig = {
  output: 'standalone',   // ← add this
  turbopack: {
    root: path.resolve(__dirname),
  },
  async rewrites() {
    if (configuredApiUrl) {
      return [];
    }

    return [
      {
        source: '/api/:path*',
        destination: 'http://localhost:8000/api/:path*',
      },
    ];
  },
};

export default nextConfig;
