import { redirect } from 'next/navigation';
import { ROUTES } from '@/lib/routes';

export default function LoginPage() {
  redirect(ROUTES.VENDOR.LOGIN);
}
