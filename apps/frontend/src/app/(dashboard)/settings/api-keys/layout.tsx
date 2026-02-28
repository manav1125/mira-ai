import { Metadata } from 'next';

export const metadata: Metadata = {
  title: 'API Keys | VentureVerse',
  description: 'Manage your API keys for programmatic access to VentureVerse',
  openGraph: {
    title: 'API Keys | VentureVerse',
    description: 'Manage your API keys for programmatic access to VentureVerse',
    type: 'website',
  },
};

export default async function APIKeysLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return <>{children}</>;
}
