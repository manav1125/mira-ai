'use client';

import { formatDistanceToNow } from 'date-fns';
import { Brain, Clock3, Trash2 } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { SpotlightCard } from '@/components/ui/spotlight-card';
import type { Memory } from '@/lib/api/memory';
import { useTranslations } from 'next-intl';

interface MemoryCardProps {
  memory: Memory;
  onDelete: (memoryId: string) => void;
  isDeleting?: boolean;
}

export function MemoryCard({ memory, onDelete, isDeleting }: MemoryCardProps) {
  const t = useTranslations('settings.memory');
  const relativeDate = memory.created_at
    ? formatDistanceToNow(new Date(memory.created_at), { addSuffix: true })
    : null;

  return (
    <SpotlightCard className="group border border-border">
      <div className="p-4 space-y-3">
        <div className="flex items-start gap-3 justify-between">
          <div className="flex-1 min-w-0 space-y-2">
            <div className="flex flex-wrap items-center gap-2">
              <Badge variant="secondary" className="rounded-full">
                <Brain className="mr-1 h-3 w-3" />
                {t(`memoryTypes.${memory.memory_type}` as any)}
              </Badge>
              {relativeDate ? (
                <span className="inline-flex items-center gap-1 text-xs text-muted-foreground">
                  <Clock3 className="h-3 w-3" />
                  {relativeDate}
                </span>
              ) : null}
            </div>

            <p className="text-sm font-medium text-foreground/90 leading-normal whitespace-pre-wrap">
              {memory.content}
            </p>
          </div>
          <Button
            variant="ghost"
            size="icon"
            onClick={() => onDelete(memory.memory_id)}
            disabled={isDeleting}
            className="h-8 w-8 text-muted-foreground/50 opacity-0 group-hover:opacity-100 hover:text-destructive hover:bg-destructive/10 transition-all"
          >
            <Trash2 className="w-4 h-4" />
          </Button>
        </div>
      </div>
    </SpotlightCard>
  );
}
