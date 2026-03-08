import { NextRequest, NextResponse } from 'next/server';

// TypeScript types for request/response
interface RegisterRequest {
  username: string;
  fullName: string;
  email: string;
  password: string;
  confirmPassword: string;
  address: string;
  nicNumber: string;
  gender: string;
  organizationCode?: string;
  businessName?: string;
  businessRegNumber?: string;
  businessAddress?: string;
  businessPhone?: string;
  businessEmail?: string;
  organizationType: 'join' | 'create';
}

interface RegisterResponse {
  status: string;
  message: string;
  data?: {
    token?: string;
    userId?: string;
  };
}

/**
 * POST /api/v1/auth/register
 * Mock vendor registration endpoint
 * 
 * Returns pending_verification status and email verification message
 */
export async function POST(request: NextRequest): Promise<NextResponse<RegisterResponse>> {
  try {
    // Parse request body
    const body: RegisterRequest = await request.json();

    // Validate required fields
    if (!body.username || !body.email || !body.password) {
      return NextResponse.json(
        {
          status: 'error',
          message: 'Missing required fields: username, email, password'
        },
        { status: 400 }
      );
    }

    // Validate password match
    if (body.password !== body.confirmPassword) {
      return NextResponse.json(
        {
          status: 'error',
          message: 'Passwords do not match'
        },
        { status: 400 }
      );
    }

    // Validate organization type
    if (!body.organizationType || !['join', 'create'].includes(body.organizationType)) {
      return NextResponse.json(
        {
          status: 'error',
          message: 'Invalid organization type'
        },
        { status: 400 }
      );
    }

    // Validate organization-specific fields
    if (body.organizationType === 'join' && !body.organizationCode) {
      return NextResponse.json(
        {
          status: 'error',
          message: 'Organization code is required when joining existing organization'
        },
        { status: 400 }
      );
    }

    if (
      body.organizationType === 'create' &&
      (!body.businessName || !body.businessRegNumber || !body.businessAddress)
    ) {
      return NextResponse.json(
        {
          status: 'error',
          message: 'Business details are required when creating new organization'
        },
        { status: 400 }
      );
    }

    // Mock: Simulate processing delay
    await new Promise((resolve) => setTimeout(resolve, 500));

    // Return success response with pending_verification status
    return NextResponse.json(
      {
        status: 'pending_verification',
        message: 'Please verify your email',
        data: {
          userId: `vendor_${Date.now()}`,
          token: `token_${Math.random().toString(36).substr(2, 9)}`
        }
      },
      { status: 200 }
    );
  } catch (error) {
    console.error('Registration error:', error);
    return NextResponse.json(
      {
        status: 'error',
        message: 'Registration failed. Please try again.'
      },
      { status: 500 }
    );
  }
}

/**
 * OPTIONS /api/v1/auth/register
 * Handle CORS preflight requests for localhost testing
 */
export async function OPTIONS(_request: NextRequest): Promise<NextResponse> {
  return new NextResponse(null, {
    status: 200,
    headers: {
      'Access-Control-Allow-Origin': 'localhost:3000',
      'Access-Control-Allow-Methods': 'POST, OPTIONS',
      'Access-Control-Allow-Headers': 'Content-Type'
    }
  });
}
