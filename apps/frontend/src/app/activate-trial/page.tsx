import { redirect } from 'next/navigation';
import { ActivateTrialPageClient } from './activate-trial-page-client';

export const dynamic = 'force-dynamic';

type SearchParams =
  | Record<string, string | string[] | undefined>
  | Promise<Record<string, string | string[] | undefined>>;

function getFirstParam(value: string | string[] | undefined): string | undefined {
  if (Array.isArray(value)) {
    return value[0];
  }

  return value;
}

export default async function ActivateTrialPage({
  searchParams,
}: {
  searchParams?: SearchParams;
}) {
  const resolvedSearchParams = searchParams ? await searchParams : {};
  const trialParam = getFirstParam(resolvedSearchParams?.trial);

  // Older success URLs can still land on /activate-trial?trial=started.
  // Redirect on the server before the page renders so checkout completion
  // reliably enters the app and the route avoids static prerendering.
  if (trialParam === 'started') {
    const params = new URLSearchParams({ trial: 'started' });
    const sessionId = getFirstParam(resolvedSearchParams?.session_id);

    if (sessionId) {
      params.set('session_id', sessionId);
    }

    redirect(`/dashboard?${params.toString()}`);
  }

  return <ActivateTrialPageClient />;
}
