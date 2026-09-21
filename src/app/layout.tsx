import type { Metadata } from 'next';
import './globals.css';

export const metadata: Metadata = {
  title: 'Equipment Operations & Decision Support',
  description: 'Advisory equipment health, telematics triage, and maintenance dispatch workspace',
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
