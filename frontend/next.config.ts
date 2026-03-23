import fs from 'fs';
import path from 'path';
import type { NextConfig } from 'next';

const fallbackEnvPath = path.resolve(__dirname, 'env');

if (fs.existsSync(fallbackEnvPath)) {
  const envLines = fs.readFileSync(fallbackEnvPath, 'utf8').split(/\r?\n/);

  for (const rawLine of envLines) {
    const line = rawLine.trim();

    if (!line || line.startsWith('#')) {
      continue;
    }

    const separatorIndex = line.indexOf('=');
    if (separatorIndex <= 0) {
      continue;
    }

    const key = line.slice(0, separatorIndex).trim();
    const value = line.slice(separatorIndex + 1).trim();

    if (!(key in process.env)) {
      process.env[key] = value;
    }
  }
}

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
