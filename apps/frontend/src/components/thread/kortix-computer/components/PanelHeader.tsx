'use client';

import { Button } from '@/components/ui/button';
import { ViewType } from '@/stores/kortix-computer-store';
import { cn } from '@/lib/utils';
import {
  Activity,
  Folder,
  Maximize2,
  Minimize2,
  Monitor,
  PanelRightClose,
  X,
} from 'lucide-react';
import { HIDE_BROWSER_TAB } from '@/components/thread/utils';

interface PanelHeaderProps {
  agentName?: string;
  onClose: () => void;
  onMaximize?: () => void;
  isStreaming?: boolean;
  variant?: 'motion' | 'drawer';
  currentView: ViewType;
  onViewChange: (view: ViewType) => void;
  showFilesTab?: boolean;
  isMaximized?: boolean;
  isSuiteMode?: boolean;
  sandboxStatus?: string;
  onToggleSuiteMode?: () => void;
}

const VIEW_OPTIONS: Array<{
  value: ViewType;
  label: string;
  icon: typeof Activity;
  hide?: boolean;
}> = [
  { value: 'tools', label: 'Actions', icon: Activity },
  { value: 'files', label: 'Files', icon: Folder },
  { value: 'browser', label: 'Browser', icon: Monitor, hide: HIDE_BROWSER_TAB },
];

export function PanelHeader({
  agentName = 'MiraComputer',
  onClose,
  onMaximize,
  isStreaming = false,
  variant = 'motion',
  currentView,
  onViewChange,
  showFilesTab = true,
  isMaximized = false,
  isSuiteMode = false,
  sandboxStatus,
  onToggleSuiteMode,
}: PanelHeaderProps) {
  const visibleViews = VIEW_OPTIONS.filter((option) => {
    if (option.hide) return false;
    if (option.value === 'files' && !showFilesTab) return false;
    return true;
  });

  return (
    <div className="flex h-14 shrink-0 items-center justify-between gap-3 border-b bg-card/95 px-3">
      <div className="flex min-w-0 items-center gap-2">
        <Button
          type="button"
          variant="ghost"
          size="icon"
          className="h-8 w-8 rounded-full"
          onClick={onClose}
          aria-label="Close computer"
        >
          {variant === 'drawer' ? <PanelRightClose className="h-4 w-4" /> : <X className="h-4 w-4" />}
        </Button>
        <div className="min-w-0">
          <div className="truncate text-sm font-semibold">{agentName}</div>
          <div className="flex items-center gap-1 text-[11px] text-muted-foreground">
            {isStreaming ? (
              <>
                <span className="h-1.5 w-1.5 rounded-full bg-emerald-500" />
                Live
              </>
            ) : sandboxStatus ? (
              <span className="truncate">{sandboxStatus}</span>
            ) : (
              <span>Ready</span>
            )}
          </div>
        </div>
      </div>

      <div className="flex items-center gap-2">
        <div className="flex rounded-full border bg-muted/40 p-1">
          {visibleViews.map((option) => {
            const Icon = option.icon;
            const selected = currentView === option.value;
            return (
              <Button
                key={option.value}
                type="button"
                variant="ghost"
                size="sm"
                onClick={() => onViewChange(option.value)}
                className={cn(
                  'h-8 rounded-full px-3 text-xs',
                  selected && 'bg-background text-foreground shadow-sm',
                )}
              >
                <Icon className="mr-1.5 h-3.5 w-3.5" />
                {option.label}
              </Button>
            );
          })}
        </div>

        {onToggleSuiteMode && (
          <Button
            type="button"
            variant="ghost"
            size="icon"
            className="h-8 w-8"
            onClick={onToggleSuiteMode}
            aria-label={isSuiteMode ? 'Exit suite mode' : 'Enter suite mode'}
          >
            {isSuiteMode ? <Minimize2 className="h-4 w-4" /> : <Maximize2 className="h-4 w-4" />}
          </Button>
        )}

        {onMaximize && (
          <Button
            type="button"
            variant="ghost"
            size="icon"
            className="h-8 w-8"
            onClick={onMaximize}
            aria-label={isMaximized ? 'Restore computer' : 'Maximize computer'}
          >
            {isMaximized ? <Minimize2 className="h-4 w-4" /> : <Maximize2 className="h-4 w-4" />}
          </Button>
        )}
      </div>
    </div>
  );
}
