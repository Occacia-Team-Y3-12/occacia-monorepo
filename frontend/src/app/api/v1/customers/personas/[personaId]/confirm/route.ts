import { NextRequest, NextResponse } from 'next/server';

const BACKEND_URL = process.env.NEXT_PUBLIC_BACKEND_URL || 'http://localhost:8000';

export async function POST(
  request: NextRequest,
  { params }: { params: { personaId: string } }
) {
  try {
    const token = request.cookies.get('auth_token')?.value;
    
    const response = await fetch(`${BACKEND_URL}/api/v1/customers/personas/${params.personaId}/confirm`, {
      method: 'POST',
      headers: {
        'Authorization': token ? `Bearer ${token}` : '',
        'Content-Type': 'application/json',
      },
    });

    const data = await response.json();
    return NextResponse.json(data, { status: response.status });
  } catch (error) {
    return NextResponse.json(
      { error: 'Failed to confirm persona' },
      { status: 500 }
    );
  }
}

export async function DELETE(
  request: NextRequest,
  { params }: { params: { personaId: string } }
) {
  try {
    const token = request.cookies.get('auth_token')?.value;
    
    const response = await fetch(`${BACKEND_URL}/api/v1/customers/personas/${params.personaId}/confirm`, {
      method: 'DELETE',
      headers: {
        'Authorization': token ? `Bearer ${token}` : '',
        'Content-Type': 'application/json',
      },
    });

    const data = await response.json();
    return NextResponse.json(data, { status: response.status });
  } catch (error) {
    return NextResponse.json(
      { error: 'Failed to unconfirm persona' },
      { status: 500 }
    );
  }
}
