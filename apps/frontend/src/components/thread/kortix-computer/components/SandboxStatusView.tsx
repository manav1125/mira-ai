'use client';

import { BrandLoader } from '@/components/ui/brand-loader';
import { Button } from '@/components/ui/button';
import { useSandboxStatusWithAutoStart } from '@/hooks/files/use-sandbox-details';
import { AlertTriangle, MonitorPlay } from 'lucide-react';

interface SandboxStatusViewProps {
  projectId?: string;
}

export function SandboxStatusView({ projectId }: SandboxStatusViewProps) {
  const { data, isLoading, refetch } = useSandboxStatusWithAutoStart(projectId);
  const status = data?.status || 'STARTING';
  const isProblemState = ['ERROR', 'STOPPED', 'ARCHIVED'].includes(status);

  return (
    <div className="flex h-full items-center justify-center bg-muted/20 p-8">
      <div className="max-w-sm text-center">
        <div className="mx-auto mb-4 flex h-14 w-14 items-center justify-center rounded-2xl border bg-background shadow-sm">
          {isProblemState ? (
            <AlertTriangle className="h-6 w-6 text-amber-500" />
          ) : (
            <MonitorPlay className="h-6 w-6 text-muted-foreground" />
          )}
        </div>
        <h3 className="text-base font-semibold">
          {isProblemState ? 'Computer needs attention' : 'Starting computer'}
        </h3>
        <p className="mt-2 text-sm text-muted-foreground">
          {isProblemState
            ? `Sandbox status is ${status}. Try refreshing or start a new run if it does not recover.`
            : `Sandbox status is ${status}. Files and browser controls will appear when it is live.`}
        </p>
        {isLoading ? (
          <div className="mt-4 flex justify-center">
            <BrandLoader size="small" />
          </div>
        ) : (
          <Button type="button" variant="outline" size="sm" className="mt-4" onClick={() => refetch()}>
            Refresh status
          </Button>
        )}
      </div>
    </div>
  );
}
