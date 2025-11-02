import type { Metadata } from 'next';
import './globals.css';

export const metadata: Metadata = {
  title: 'Echo Dashboard',
  description: 'Unified control center for EchoOS, Echo Computer, and Neon banking.',
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
