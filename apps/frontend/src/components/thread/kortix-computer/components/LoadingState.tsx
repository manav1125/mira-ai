'use client';

import { Button } from '@/components/ui/button';
import { BrandLoader } from '@/components/ui/brand-loader';
import { X } from 'lucide-react';

interface LoadingStateProps {
  agentName?: string;
  onClose: () => void;
  isMobile?: boolean;
}

export function LoadingState({ agentName = 'MiraComputer', onClose, isMobile = false }: LoadingStateProps) {
  return (
    <div className="flex h-full flex-col overflow-hidden rounded-3xl border bg-card">
      <div className="flex h-14 shrink-0 items-center justify-between border-b px-3">
        <div className="text-sm font-semibold">{agentName}</div>
        <Button type="button" variant="ghost" size="icon" className="h-8 w-8" onClick={onClose}>
          <X className="h-4 w-4" />
        </Button>
      </div>
      <div className="flex flex-1 items-center justify-center p-8">
        <div className="text-center">
          <BrandLoader size={isMobile ? 'small' : 'medium'} />
          <p className="mt-4 text-sm text-muted-foreground">Starting computer...</p>
        </div>
      </div>
    </div>
  );
}
