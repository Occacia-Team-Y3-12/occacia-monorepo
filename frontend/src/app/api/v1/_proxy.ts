import { NextRequest, NextResponse } from 'next/server';

import { featureFlags } from '@/config/featureFlags';

function getBackendApiBaseUrl() {
  const configuredBaseUrl =
    process.env.NEXT_PUBLIC_API_URL?.trim() || 'http://localhost:8000';
  const normalizedBaseUrl = configuredBaseUrl.replace(/\/+$/, '');

  return normalizedBaseUrl.endsWith('/api/v1')
    ? normalizedBaseUrl
    : `${normalizedBaseUrl}/api/v1`;
}

export const shouldUseCustomerPlanningMockApi = () =>
  featureFlags.useCustomerPlanningMockApi;

export async function proxyApiRequest(
  request: Request | NextRequest,
  backendPath: string
) {
  const incomingUrl = new URL(request.url);
  const targetUrl = new URL(`${getBackendApiBaseUrl()}${backendPath}`);
  targetUrl.search = incomingUrl.search;

  const headers = new Headers(request.headers);
  headers.delete('host');
  headers.delete('connection');
  headers.delete('content-length');

  const method = request.method.toUpperCase();
  const init: RequestInit = {
    method,
    headers,
    redirect: 'manual',
  };

  if (method !== 'GET' && method !== 'HEAD') {
    init.body = await request.arrayBuffer();
  }

  const response = await fetch(targetUrl, init);
  const responseHeaders = new Headers(response.headers);
  responseHeaders.delete('content-length');
  responseHeaders.delete('connection');
  responseHeaders.delete('content-encoding');

  return new NextResponse(response.body, {
    status: response.status,
    headers: responseHeaders,
  });
}
