import { NextRequest, NextResponse } from 'next/server';
import { proxyApiRequest } from '@/app/api/v1/_proxy';

type RouteContext = {
  params: Promise<{
    path?: string[];
  }>;
};

const toBackendPath = async (context: RouteContext) => {
  const { path = [] } = await context.params;
  return `/${path.join('/')}`;
};

async function handle(
  request: NextRequest,
  context: RouteContext
): Promise<NextResponse> {
  const backendPath = await toBackendPath(context);
  return proxyApiRequest(request, backendPath);
}

export async function GET(
  request: NextRequest,
  context: RouteContext
): Promise<NextResponse> {
  return handle(request, context);
}

export async function POST(
  request: NextRequest,
  context: RouteContext
): Promise<NextResponse> {
  return handle(request, context);
}

export async function PUT(
  request: NextRequest,
  context: RouteContext
): Promise<NextResponse> {
  return handle(request, context);
}

export async function PATCH(
  request: NextRequest,
  context: RouteContext
): Promise<NextResponse> {
  return handle(request, context);
}

export async function DELETE(
  request: NextRequest,
  context: RouteContext
): Promise<NextResponse> {
  return handle(request, context);
}

export async function HEAD(
  request: NextRequest,
  context: RouteContext
): Promise<NextResponse> {
  return handle(request, context);
}

export async function OPTIONS(
  request: NextRequest,
  context: RouteContext
): Promise<NextResponse> {
  return handle(request, context);
}
