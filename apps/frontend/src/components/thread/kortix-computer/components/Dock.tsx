'use client';

import { Button } from '@/components/ui/button';
import { ToolCallInput } from '../KortixComputer';
import { getUserFriendlyToolName } from '@/components/thread/utils';
import { ChevronLeft, ChevronRight, Radio } from 'lucide-react';
import { cn } from '@/lib/utils';

interface AppDockProps {
  toolCalls: ToolCallInput[];
  currentIndex: number;
  onNavigate: (index: number) => void;
  onPrevious: () => void;
  onNext: () => void;
  latestIndex: number;
  agentStatus: string;
  isLiveMode: boolean;
  onJumpToLive: () => void;
  onJumpToLatest: () => void;
}

export function AppDock({
  toolCalls,
  currentIndex,
  onNavigate,
  onPrevious,
  onNext,
  latestIndex,
  agentStatus,
  isLiveMode,
  onJumpToLive,
  onJumpToLatest,
}: AppDockProps) {
  return (
    <div className="fixed bottom-4 left-1/2 z-[10000] flex max-w-[min(900px,calc(100vw-2rem))] -translate-x-1/2 items-center gap-2 rounded-2xl border bg-background/90 p-2 shadow-2xl backdrop-blur">
      <Button type="button" variant="ghost" size="icon" onClick={onPrevious} disabled={currentIndex <= 0}>
        <ChevronLeft className="h-4 w-4" />
      </Button>
      <div className="flex max-w-[60vw] gap-1 overflow-x-auto">
        {toolCalls.map((call, index) => {
          const name = getUserFriendlyToolName(call.toolCall?.function_name || 'Tool');
          return (
            <Button
              key={`${call.toolCall?.tool_call_id || 'tool'}-${index}`}
              type="button"
              variant="ghost"
              size="sm"
              onClick={() => onNavigate(index)}
              className={cn(
                'h-9 max-w-36 shrink-0 rounded-xl px-3 text-xs',
                index === currentIndex && 'bg-primary text-primary-foreground',
              )}
              title={name}
            >
              <span className="truncate">{name}</span>
            </Button>
          );
        })}
      </div>
      <Button type="button" variant="ghost" size="icon" onClick={onNext} disabled={currentIndex >= latestIndex}>
        <ChevronRight className="h-4 w-4" />
      </Button>
      <Button
        type="button"
        variant={isLiveMode ? 'secondary' : 'outline'}
        size="sm"
        className="h-9 rounded-xl text-xs"
        onClick={agentStatus === 'running' ? onJumpToLive : onJumpToLatest}
      >
        <Radio className="mr-1.5 h-3.5 w-3.5" />
        {agentStatus === 'running' ? (isLiveMode ? 'Live' : 'Live') : 'Latest'}
      </Button>
    </div>
  );
}
