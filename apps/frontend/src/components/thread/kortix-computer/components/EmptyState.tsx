'use client';

import { Activity } from 'lucide-react';

interface EmptyStateProps {
  t?: (key: string) => string;
}

export function EmptyState({ t }: EmptyStateProps) {
  return (
    <div className="flex h-full items-center justify-center bg-muted/20 p-8">
      <div className="max-w-sm text-center">
        <div className="mx-auto mb-4 flex h-14 w-14 items-center justify-center rounded-2xl border bg-background shadow-sm">
          <Activity className="h-6 w-6 text-muted-foreground" />
        </div>
        <h3 className="text-base font-semibold">
          {t?.('computer.emptyTitle') || 'Worker actions will appear here'}
        </h3>
        <p className="mt-2 text-sm text-muted-foreground">
          {t?.('computer.emptyDescription') || 'Tools, files, and browser activity show up as Mira works.'}
        </p>
      </div>
    </div>
  );
}
