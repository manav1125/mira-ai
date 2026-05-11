'use client';

import { Button } from '@/components/ui/button';
import { Slider } from '@/components/ui/slider';
import { ChevronLeft, ChevronRight } from 'lucide-react';

interface NavigationControlsProps {
  displayIndex: number;
  displayTotalCalls: number;
  safeInternalIndex: number;
  latestIndex: number;
  isLiveMode: boolean;
  agentStatus: string;
  onPrevious: () => void;
  onNext: () => void;
  onSliderChange: (value: number[]) => void;
  onJumpToLive: () => void;
  onJumpToLatest: () => void;
  isMobile?: boolean;
}

export function NavigationControls({
  displayIndex,
  displayTotalCalls,
  safeInternalIndex,
  latestIndex,
  isLiveMode,
  agentStatus,
  onPrevious,
  onNext,
  onSliderChange,
  onJumpToLive,
  onJumpToLatest,
  isMobile = false,
}: NavigationControlsProps) {
  const isRunning = agentStatus === 'running';

  return (
    <div className="flex shrink-0 items-center gap-3 border-t bg-card/95 px-3 py-2">
      <Button
        type="button"
        variant="ghost"
        size="icon"
        className="h-8 w-8"
        onClick={onPrevious}
        disabled={safeInternalIndex <= 0}
        aria-label="Previous action"
      >
        <ChevronLeft className="h-4 w-4" />
      </Button>

      <div className="min-w-[3.5rem] text-center text-xs text-muted-foreground">
        {displayIndex + 1}/{Math.max(displayTotalCalls, 1)}
      </div>

      {!isMobile && (
        <Slider
          value={[safeInternalIndex]}
          min={0}
          max={Math.max(latestIndex, 0)}
          step={1}
          onValueChange={onSliderChange}
          className="min-w-0 flex-1"
        />
      )}

      <Button
        type="button"
        variant="ghost"
        size="icon"
        className="h-8 w-8"
        onClick={onNext}
        disabled={safeInternalIndex >= latestIndex}
        aria-label="Next action"
      >
        <ChevronRight className="h-4 w-4" />
      </Button>

      <Button
        type="button"
        variant={isLiveMode ? 'secondary' : 'outline'}
        size="sm"
        className="h-8 rounded-full text-xs"
        onClick={isRunning ? onJumpToLive : onJumpToLatest}
      >
        {isRunning ? (isLiveMode ? 'Live' : 'Jump to Live') : 'Latest'}
      </Button>
    </div>
  );
}
