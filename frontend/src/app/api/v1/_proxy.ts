import { NextRequest, NextResponse } from 'next/server';

function getBackendApiBaseUrl() {
  // Default to 'backend:8000' for Docker container networking
  // Can be overridden with NEXT_PUBLIC_BACKEND_URL or NEXT_PUBLIC_API_URL
  const defaultUrl = process.env.NODE_ENV === 'production' ? 'http://backend:8000' : 'http://localhost:8000';
  
  const configuredBaseUrl =
    process.env.NEXT_PUBLIC_BACKEND_URL?.trim() ||
    process.env.NEXT_PUBLIC_API_URL?.trim() ||
    defaultUrl;
  const normalizedBaseUrl = configuredBaseUrl.replace(/\/+$/, '');

  return normalizedBaseUrl.endsWith('/api/v1')
    ? normalizedBaseUrl
    : `${normalizedBaseUrl}/api/v1`;
}

export const envFlag = (value: string | undefined, defaultValue = false) => {
  if (value == null) {
    return defaultValue;
  }

  return value.trim().toLowerCase() === 'true';
};

export const shouldUseCustomerPlanningMockApi = () => {
  const enableFrontendMocks = envFlag(
    process.env.NEXT_PUBLIC_ENABLE_FRONTEND_MOCKS
  );

  return envFlag(
    process.env.NEXT_PUBLIC_USE_CUSTOMER_PLANNING_MOCK_API,
    enableFrontendMocks
  );
};

export const shouldUseVendorAuthMock = () => {
  const enableFrontendMocks = envFlag(
    process.env.NEXT_PUBLIC_ENABLE_FRONTEND_MOCKS
  );

  return envFlag(
    process.env.NEXT_PUBLIC_USE_VENDOR_AUTH_MOCK,
    enableFrontendMocks
  );
};

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

  const fetchWithRetry = async () => {
    const attempts = 2;
    for (let attempt = 1; attempt <= attempts; attempt += 1) {
      try {
        return await fetch(targetUrl, init);
      } catch (error) {
        if (attempt === attempts) {
          throw error;
        }
      }
    }

    throw new Error('Proxy fetch failed after retries.');
  };

  try {
    const response = await fetchWithRetry();
    const responseHeaders = new Headers(response.headers);
    responseHeaders.delete('content-length');
    responseHeaders.delete('connection');
    responseHeaders.delete('content-encoding');

    return new NextResponse(response.body, {
      status: response.status,
      headers: responseHeaders,
    });
  } catch (error) {
    console.error(`Failed to proxy ${targetUrl.toString()}`, error);

    return NextResponse.json(
      {
        message: 'Unable to reach backend API.',
        backendUrl: targetUrl.toString(),
      },
      { status: 502 }
    );
  }
}
