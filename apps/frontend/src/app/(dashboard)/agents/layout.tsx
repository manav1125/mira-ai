import { Metadata } from 'next';
import { redirect } from 'next/navigation';

export const metadata: Metadata = {
  title: 'Worker Conversation | VentureVerse',
  description: 'Interactive Worker conversation powered by VentureVerse',
  openGraph: {
    title: 'Worker Conversation | VentureVerse',
    description: 'Interactive Worker conversation powered by VentureVerse',
    type: 'website',
  },
};

export default async function AgentsLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return <>{children}</>;
}
