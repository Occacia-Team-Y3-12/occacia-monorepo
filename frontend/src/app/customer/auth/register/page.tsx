'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import Link from 'next/link';
import Image from 'next/image';
import { toast } from 'sonner';
import { Mail } from 'lucide-react';

import Button from '@/components/ui/Button';
import RegisterForm from '@/components/customer/auth/RegisterForm';
import SocialLoginButtons from '@/components/ui/SocialLoginButtons';
import { RegisterFormValues } from '@/lib/validators';
import { customerAuthService } from '@/services/customer/authServices';

export default function RegisterPage() {
  const router = useRouter();
  const [isLoading, setIsLoading] = useState(false);
  const [registeredEmail, setRegisteredEmail] = useState<string | null>(null);

  const onSubmit = async (data: RegisterFormValues) => {
    setIsLoading(true);

    try {
      await customerAuthService.register(data);
      setRegisteredEmail(data.email);
      toast.success('Registration successful! Please check your email.');
    } catch (error: any) {
      const errorMessage = error.response?.data?.message || 'Registration failed. Please try again.';
      
      if (error.response?.status === 409) {
        toast.error('An account already exists with this email address.');
      } else if (error.response?.data?.errors) {
        const errors = error.response.data.errors;
        Object.keys(errors).forEach((field) => {
          toast.error(`${field}: ${errors[field].join(', ')}`);
        });
      } else {
        toast.error(errorMessage);
      }
    } finally {
      setIsLoading(false);
    }
  };

  // Check Your Email Screen
  if (registeredEmail) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-gray-50 to-gray-100 px-4">
        <div className="max-w-md w-full bg-white rounded-3xl shadow-xl p-8 text-center">
          <div className="w-20 h-20 bg-green-100 rounded-full flex items-center justify-center mx-auto mb-6">
            <Mail className="w-10 h-10 text-green-600" />
          </div>
          <h1 className="text-3xl font-bold text-gray-900 mb-3">Check Your Email</h1>
          <p className="text-gray-600 mb-2">
            We've sent a verification link to
          </p>
          <p className="font-semibold text-gray-900 mb-6">{registeredEmail}</p>
          <p className="text-sm text-gray-500 mb-8">
            Please click the link in the email to verify your account. 
            If you don't see the email, check your spam folder.
          </p>
          <Button
            onClick={() => router.push('/customer/auth/login')}
            variant="primary"
            className="w-full"
          >
            Go to Login
          </Button>
        </div>
      </div>
    );
  }

  // Registration Form Screen
  return (
    <div className="min-h-screen flex items-center justify-center px-4 bg-cover bg-center bg-no-repeat" style={{ backgroundImage: "url('/images/customer/background.jpeg')" }}>
      <div className="w-full max-w-4xl bg-white/95 backdrop-blur rounded-xl shadow-xl flex overflow-hidden">
        
        {/* Left Section - Form */}
        <div className="flex-1 p-8">
          <div className="flex items-center gap-2 mb-6">
            <div className="w-10 h-10 bg-gradient-to-br from-blue-500 via-blue-600 to-cyan-500 rounded-lg flex items-center justify-center shadow-md">
              <span className="text-white font-bold text-xl">O</span>
            </div>
            <span className="text-2xl font-bold text-gray-900">OCCACIA</span>
          </div>

          <div className="mb-6">
            <h1 className="text-2xl font-semibold text-gray-900 mb-1">Create an account</h1>
            <p className="text-gray-500 text-sm">Let's create magic together.</p>
          </div>

          <RegisterForm onSubmit={onSubmit} isLoading={isLoading} />

          <div className="mt-4 space-y-2">
            <SocialLoginButtons />
          </div>

          <p className="text-sm text-center text-gray-500 mt-4">
            Already have an account?{' '}
            <Link href="/customer/auth/login" className="text-blue-600 cursor-pointer hover:underline">
              Login
            </Link>
          </p>
        </div>

        {/* Right Section - Image */}
        <div className="relative hidden md:block w-80 flex-shrink-0">
          <Image
            src="/images/customer/customer register pic.png"
            alt="Customer Register"
            fill
            className="object-cover rounded-r-xl"
            priority
          />
          <div className="absolute inset-0 bg-black/40 flex items-center justify-center px-6 rounded-r-xl">
            <h2 className="text-white text-2xl font-semibold leading-snug text-center">
              <span className="text-yellow-300 text-3xl">P</span>lan<br />
              meaningful<br />
              moments,<br />
              effortlessly with<br />
              <span className="text-3xl font-bold">Occacia</span>
            </h2>
          </div>
        </div>
      </div>
    </div>
  );
}