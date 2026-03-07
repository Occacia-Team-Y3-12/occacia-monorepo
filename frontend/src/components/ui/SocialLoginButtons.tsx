// src/components/customer/auth/SocialLoginButtons.tsx
'use client';

import Image from 'next/image';

export default function SocialLoginButtons() {
  const handleGoogleSignup = () => {
    console.log('Google signup');
  };

  const handleFacebookSignup = () => {
    console.log('Facebook signup');
  };

  return (
    <div className="flex gap-3 mt-4">
      <button
        type="button"
        onClick={handleGoogleSignup}
        className="flex-1 flex items-center justify-center gap-2 border border-gray-300 rounded-md py-2 text-sm hover:bg-gray-50 transition"
      >
        <Image src="/images/customer/google.png" alt="Google" width={20} height={20} />
        Sign up with Google
      </button>

      <button
        type="button"
        onClick={handleFacebookSignup}
        className="flex-1 flex items-center justify-center gap-2 border border-gray-300 rounded-md py-2 text-sm hover:bg-gray-50 transition"
      >
        <Image src="/images/customer/fb.png" alt="Facebook" width={20} height={20} />
        Sign up with Facebook
      </button>
    </div>
  );
}