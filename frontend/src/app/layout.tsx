import type { Metadata } from 'next';
import './globals.css';

export const metadata: Metadata = {
  title: 'OCCACIA',
  description: 'OCCACIA Application',
  icons: {
    icon: '/images/customer/logo.png',
  },
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
