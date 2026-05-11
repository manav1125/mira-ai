'use client';

import { Button } from '@/components/ui/button';
import { ViewType } from '@/stores/kortix-computer-store';
import { ToolCallInput } from '../KortixComputer';
import { ToolView } from '../../tool-views/wrapper';
import { ApiMessageType } from '@/components/thread/types';
import { Project } from '@/lib/api/threads';
import { AppDock } from './Dock';
import { Activity, Folder, Globe, X } from 'lucide-react';
import { HIDE_BROWSER_TAB } from '@/components/thread/utils';
import { cn } from '@/lib/utils';

interface SandboxDesktopProps {
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
  project?: Project;
  messages?: ApiMessageType[];
  onFileClick?: (filePath: string) => void;
  streamingText?: string;
  onClose: () => void;
  currentView: ViewType;
  onViewChange: (view: ViewType) => void;
  renderFilesView: () => React.ReactNode;
  renderBrowserView: () => React.ReactNode;
  isStreaming: boolean;
  project_id?: string;
}

const DESKTOP_VIEWS: Array<{ value: ViewType; label: string; icon: typeof Activity; hidden?: boolean }> = [
  { value: 'tools', label: 'Actions', icon: Activity },
  { value: 'files', label: 'Files', icon: Folder },
  { value: 'browser', label: 'Browser', icon: Globe, hidden: HIDE_BROWSER_TAB },
];

export function SandboxDesktop({
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
  project,
  messages,
  onFileClick,
  streamingText,
  onClose,
  currentView,
  onViewChange,
  renderFilesView,
  renderBrowserView,
  isStreaming,
}: SandboxDesktopProps) {
  const currentTool = toolCalls[currentIndex];
  const isCurrentStreaming = currentTool?.toolResult === undefined && isStreaming;

  const renderMainContent = () => {
    if (currentView === 'files') return renderFilesView();
    if (currentView === 'browser') return renderBrowserView();
    if (!currentTool?.toolCall) {
      return (
        <div className="flex h-full items-center justify-center text-sm text-muted-foreground">
          No actions yet.
        </div>
      );
    }

    return (
      <ToolView
        toolCall={currentTool.toolCall}
        toolResult={currentTool.toolResult}
        assistantTimestamp={currentTool.assistantTimestamp}
        toolTimestamp={currentTool.toolTimestamp}
        isSuccess={isCurrentStreaming ? true : (currentTool.toolResult?.success ?? currentTool.isSuccess ?? true)}
        isStreaming={isCurrentStreaming}
        project={project}
        messages={messages}
        agentStatus={agentStatus}
        currentIndex={currentIndex}
        totalCalls={toolCalls.length}
        onFileClick={onFileClick}
        streamingText={isCurrentStreaming ? streamingText : undefined}
      />
    );
  };

  return (
    <div className="flex h-full flex-col overflow-hidden bg-background">
      <div className="flex h-14 shrink-0 items-center justify-between border-b px-4">
        <div className="flex items-center gap-2">
          {DESKTOP_VIEWS.filter((view) => !view.hidden).map((view) => {
            const Icon = view.icon;
            return (
              <Button
                key={view.value}
                type="button"
                variant="ghost"
                size="sm"
                onClick={() => onViewChange(view.value)}
                className={cn(currentView === view.value && 'bg-muted')}
              >
                <Icon className="mr-1.5 h-4 w-4" />
                {view.label}
              </Button>
            );
          })}
        </div>
        <Button type="button" variant="ghost" size="icon" onClick={onClose} aria-label="Close maximized computer">
          <X className="h-4 w-4" />
        </Button>
      </div>
      <div className="min-h-0 flex-1 overflow-hidden">
        {renderMainContent()}
      </div>
      {currentView === 'tools' && (
        <AppDock
          toolCalls={toolCalls}
          currentIndex={currentIndex}
          onNavigate={onNavigate}
          onPrevious={onPrevious}
          onNext={onNext}
          latestIndex={latestIndex}
          agentStatus={agentStatus}
          isLiveMode={isLiveMode}
          onJumpToLive={onJumpToLive}
          onJumpToLatest={onJumpToLatest}
        />
      )}
    </div>
  );
}
