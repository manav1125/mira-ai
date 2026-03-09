'use client';

import { useState } from 'react';
import { AlertTriangle, Brain, Database, Sparkles, Trash2 } from 'lucide-react';
import { useTranslations } from 'next-intl';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Button } from '@/components/ui/button';
import { Card, CardContent } from '@/components/ui/card';
import { Switch } from '@/components/ui/switch';
import { Skeleton } from '@/components/ui/skeleton';
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
  AlertDialogTrigger,
} from '@/components/ui/alert-dialog';
import { MemoryList } from './MemoryList';
import {
  useDeleteAllMemories,
  useDeleteMemory,
  useInfiniteMemories,
  useMemorySettings,
  useMemoryStats,
  useUpdateMemorySettings,
} from '@/hooks/memory/use-memory';

export function MemorySettings() {
  const t = useTranslations('settings.memory');
  const [deletingIds, setDeletingIds] = useState<Set<string>>(new Set());

  const statsQuery = useMemoryStats();
  const settingsQuery = useMemorySettings();
  const memoriesQuery = useInfiniteMemories(25);
  const updateSettings = useUpdateMemorySettings();
  const deleteAllMutation = useDeleteAllMemories();
  const deleteMemoryMutation = useDeleteMemory();

  const memories = memoriesQuery.data?.pages.flatMap((page) => page.memories) ?? [];
  const totalMemories = statsQuery.data?.total_memories ?? memories.length;
  const maxMemories = statsQuery.data?.max_memories ?? 0;
  const retrievalLimit = statsQuery.data?.retrieval_limit ?? 0;
  const tierName = statsQuery.data?.tier_name ?? 'free';
  const userMemoryEnabled = settingsQuery.data?.memory_enabled ?? false;
  const featureAvailable = maxMemories > 0 || totalMemories > 0;
  const hasMore = Boolean(memoriesQuery.hasNextPage);

  const handleToggleMemory = (enabled: boolean) => {
    updateSettings.mutate(enabled);
  };

  const handleDeleteMemory = async (memoryId: string) => {
    setDeletingIds((current) => new Set(current).add(memoryId));
    try {
      await deleteMemoryMutation.mutateAsync(memoryId);
    } finally {
      setDeletingIds((current) => {
        const next = new Set(current);
        next.delete(memoryId);
        return next;
      });
    }
  };

  return (
    <div className="p-4 sm:p-6 pb-12 sm:pb-6 space-y-5 sm:space-y-6 min-w-0 max-w-full overflow-x-hidden">
      <div className="flex items-start justify-between gap-4">
        <div className="space-y-1">
          <div className="flex items-center gap-3">
            <div className="p-2 rounded-xl bg-primary/10">
              <Brain className="h-5 w-5 text-primary" />
            </div>
            <div>
              <h3 className="text-lg font-semibold">{t('title')}</h3>
              <p className="text-sm text-muted-foreground mt-0.5">
                {t('description')}
              </p>
            </div>
          </div>
        </div>

        {settingsQuery.isLoading ? (
          <Skeleton className="h-10 w-16 rounded-full" />
        ) : (
          <div className="flex items-center gap-3 rounded-2xl border px-3 py-2">
            <div className="text-right">
              <div className="text-sm font-medium">
                {userMemoryEnabled ? t('enabled') : t('disabled')}
              </div>
              <div className="text-xs text-muted-foreground">
                {featureAvailable ? tierName : t('upgradeRequired')}
              </div>
            </div>
            <Switch
              checked={userMemoryEnabled}
              onCheckedChange={handleToggleMemory}
              disabled={!featureAvailable || updateSettings.isPending}
              aria-label={t('enableMemory')}
            />
          </div>
        )}
      </div>

      {statsQuery.isLoading ? (
        <div className="grid gap-3 md:grid-cols-3">
          {Array.from({ length: 3 }).map((_, index) => (
            <Skeleton key={index} className="h-28 rounded-2xl" />
          ))}
        </div>
      ) : (
        <div className="grid gap-3 md:grid-cols-3">
          <Card className="rounded-2xl">
            <CardContent className="p-4 space-y-1">
              <p className="text-sm text-muted-foreground">{t('usage')}</p>
              <div className="text-2xl font-semibold">{totalMemories}</div>
              <p className="text-xs text-muted-foreground">
                {featureAvailable && maxMemories > 0
                  ? `${totalMemories}/${maxMemories} ${t('available', { count: maxMemories })}`
                  : t('notAvailable')}
              </p>
            </CardContent>
          </Card>
          <Card className="rounded-2xl">
            <CardContent className="p-4 space-y-1">
              <p className="text-sm text-muted-foreground">Retrieval limit</p>
              <div className="text-2xl font-semibold">{retrievalLimit}</div>
              <p className="text-xs text-muted-foreground">
                Relevant memories injected into future chats
              </p>
            </CardContent>
          </Card>
          <Card className="rounded-2xl">
            <CardContent className="p-4 space-y-1">
              <p className="text-sm text-muted-foreground">Plan</p>
              <div className="text-2xl font-semibold capitalize">{tierName}</div>
              <p className="text-xs text-muted-foreground">
                Memory capacity is based on the current tier
              </p>
            </CardContent>
          </Card>
        </div>
      )}

      {!featureAvailable ? (
        <Alert className="border-amber-500/30 bg-amber-500/5">
          <AlertTriangle className="h-4 w-4 text-amber-600" />
          <AlertDescription className="text-sm">
            {t('notAvailable')}
          </AlertDescription>
        </Alert>
      ) : !userMemoryEnabled ? (
        <Alert className="border-primary/20 bg-primary/5">
          <Sparkles className="h-4 w-4 text-primary" />
          <AlertDescription className="text-sm">
            {t('memoryDisabledByUser')}
          </AlertDescription>
        </Alert>
      ) : (
        <Alert className="border-primary/20 bg-primary/5">
          <Database className="h-4 w-4 text-primary" />
          <AlertDescription className="text-sm">
            {t('enableMemoryDescription')}
          </AlertDescription>
        </Alert>
      )}

      <div className="space-y-4">
        <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
          <div>
            <h4 className="text-base font-semibold">{t('yourMemories')}</h4>
            <p className="text-sm text-muted-foreground">
              {t('yourMemoriesDescription')}
            </p>
          </div>

          <AlertDialog>
            <AlertDialogTrigger asChild>
              <Button
                variant="outline"
                className="rounded-xl"
                disabled={deleteAllMutation.isPending || memories.length === 0}
              >
                <Trash2 className="mr-2 h-4 w-4" />
                {t('clearAll')}
              </Button>
            </AlertDialogTrigger>
            <AlertDialogContent>
              <AlertDialogHeader>
                <AlertDialogTitle>{t('deleteAllTitle')}</AlertDialogTitle>
                <AlertDialogDescription>
                  {t('deleteAllDescription', { count: totalMemories })}
                </AlertDialogDescription>
              </AlertDialogHeader>
              <AlertDialogFooter>
                <AlertDialogCancel>Cancel</AlertDialogCancel>
                <AlertDialogAction
                  onClick={() => deleteAllMutation.mutate()}
                  className="bg-destructive text-destructive-foreground hover:bg-destructive/90"
                >
                  {t('deleteAllButton')}
                </AlertDialogAction>
              </AlertDialogFooter>
            </AlertDialogContent>
          </AlertDialog>
        </div>

        <MemoryList
          memories={memories}
          isLoading={memoriesQuery.isLoading || memoriesQuery.isFetchingNextPage}
          error={
            statsQuery.error instanceof Error
              ? statsQuery.error.message
              : settingsQuery.error instanceof Error
                ? settingsQuery.error.message
                : memoriesQuery.error instanceof Error
                  ? memoriesQuery.error.message
                  : null
          }
          onDelete={handleDeleteMemory}
          onLoadMore={() => memoriesQuery.fetchNextPage()}
          hasMore={hasMore}
          deletingIds={deletingIds}
        />
      </div>
    </div>
  );
}
