'use client';

import React, { memo, useCallback, useEffect, useMemo, useRef, useState } from 'react';
import { AudioLines, Loader2, MicOff, PhoneOff, PhoneOutgoing } from 'lucide-react';

import { Button } from '@/components/ui/button';
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle } from '@/components/ui/dialog';
import { Tooltip, TooltipContent, TooltipTrigger } from '@/components/ui/tooltip';
import { backendApi } from '@/lib/api-client';

type ConnectionState = 'idle' | 'connecting' | 'connected' | 'error';

interface TranscriptPreview {
  role: 'user' | 'assistant';
  text: string;
}

interface VapiSessionResponse {
  public_key: string;
  assistant: Record<string, unknown>;
  thread_id: string;
  agent_id?: string | null;
  agent_name?: string | null;
}

interface LiveVoiceButtonProps {
  threadId: string;
  selectedAgentId?: string;
  disabled?: boolean;
}

export const LiveVoiceButton: React.FC<LiveVoiceButtonProps> = memo(function LiveVoiceButton({
  threadId,
  selectedAgentId,
  disabled = false,
}) {
  const [open, setOpen] = useState(false);
  const [connectionState, setConnectionState] = useState<ConnectionState>('idle');
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [statusText, setStatusText] = useState('Ready to start a live conversation.');
  const [isMuted, setIsMuted] = useState(false);
  const [transcriptPreview, setTranscriptPreview] = useState<TranscriptPreview[]>([]);
  const [activeAgentName, setActiveAgentName] = useState<string>('Mira');

  const vapiRef = useRef<any>(null);
  const persistedKeysRef = useRef<Set<string>>(new Set());
  const mountedRef = useRef(true);

  useEffect(() => {
    return () => {
      mountedRef.current = false;
      if (vapiRef.current) {
        try {
          vapiRef.current.stop();
        } catch (error) {
          console.warn('Failed to stop Vapi session on unmount', error);
        }
      }
    };
  }, []);

  const stopSession = useCallback(async () => {
    if (!vapiRef.current) {
      setConnectionState('idle');
      setIsMuted(false);
      return;
    }

    try {
      await vapiRef.current.stop();
    } catch (error) {
      console.warn('Failed to stop Vapi session cleanly', error);
    } finally {
      vapiRef.current = null;
      persistedKeysRef.current.clear();
      if (mountedRef.current) {
        setConnectionState('idle');
        setStatusText('Voice session ended.');
        setIsMuted(false);
      }
    }
  }, []);

  const persistTranscript = useCallback(async (message: any) => {
    const transcript = String(message?.transcript || '').trim();
    const role = message?.role === 'assistant' ? 'assistant' : 'user';
    if (!transcript) {
      return;
    }

    const dedupeKey = [
      message?.call?.id || 'no-call',
      role,
      String(message?.timestamp ?? ''),
      transcript,
    ].join('::');

    if (persistedKeysRef.current.has(dedupeKey)) {
      return;
    }
    persistedKeysRef.current.add(dedupeKey);

    setTranscriptPreview((current) => [
      ...current.slice(-5),
      { role, text: transcript },
    ]);

    const response = await backendApi.post(
      `/vapi/web/transcript/${threadId}`,
      {
        role,
        transcript,
        call_id: message?.call?.id ?? null,
        dedupe_key: dedupeKey,
        timestamp: message?.timestamp ?? null,
        agent_id: role === 'assistant' ? selectedAgentId ?? null : null,
      },
      {
        showErrors: false,
        timeout: 15000,
      }
    );

    if (response.error) {
      console.error('Failed to persist live voice transcript turn', response.error);
    }
  }, [selectedAgentId, threadId]);

  const handleVapiMessage = useCallback((message: any) => {
    const type = String(message?.type || '');

    if (type.startsWith('transcript')) {
      const transcriptType = message?.transcriptType;
      if (transcriptType === 'final' || type === "transcript[transcriptType='final']") {
        void persistTranscript(message);
      }
      return;
    }

    if (type === 'status-update' && message?.status) {
      setStatusText(`Status: ${message.status}`);
    }
  }, [persistTranscript]);

  const startSession = useCallback(async () => {
    setConnectionState('connecting');
    setErrorMessage(null);
    setStatusText('Preparing live voice...');
    setTranscriptPreview([]);
    persistedKeysRef.current.clear();

    const sessionResponse = await backendApi.post<VapiSessionResponse>(
      `/vapi/web/session/${threadId}`,
      {
        agent_id: selectedAgentId ?? null,
      },
      {
        showErrors: false,
        timeout: 20000,
      }
    );

    if (sessionResponse.error || !sessionResponse.data) {
      const detail = sessionResponse.error?.message || 'Unable to start live voice right now.';
      setConnectionState('error');
      setErrorMessage(detail);
      setStatusText('Live voice could not start.');
      return;
    }

    setActiveAgentName(sessionResponse.data.agent_name || 'Mira');

    try {
      const { default: Vapi } = await import('@vapi-ai/web');
      const vapi = new Vapi(sessionResponse.data.public_key);
      vapiRef.current = vapi;

      vapi.on('call-start', () => {
        if (!mountedRef.current) return;
        setConnectionState('connected');
        setStatusText(`Live with ${sessionResponse.data?.agent_name || 'Mira'}.`);
      });

      vapi.on('call-end', () => {
        if (!mountedRef.current) return;
        vapiRef.current = null;
        persistedKeysRef.current.clear();
        setConnectionState('idle');
        setIsMuted(false);
        setStatusText('Voice session ended.');
      });

      vapi.on('speech-start', () => {
        if (!mountedRef.current) return;
        setStatusText(`${sessionResponse.data?.agent_name || 'Mira'} is speaking...`);
      });

      vapi.on('speech-end', () => {
        if (!mountedRef.current) return;
        setStatusText(isMuted ? 'Muted' : 'Listening...');
      });

      vapi.on('message', (message: any) => {
        void handleVapiMessage(message);
      });

      vapi.on('call-start-failed', (event: any) => {
        console.error('Vapi live voice call-start-failed', event);
        if (!mountedRef.current) return;
        const detail =
          event?.error ||
          event?.context?.error ||
          event?.context?.message ||
          'Live voice failed to connect.';
        setConnectionState('error');
        setErrorMessage(String(detail));
        setStatusText('Live voice could not connect.');
      });

      vapi.on('error', (error: any) => {
        console.error('Vapi live voice error', error);
        if (!mountedRef.current) return;
        const detail =
          error?.message ||
          error?.error?.message ||
          error?.errorMsg ||
          error?.error ||
          'Live voice hit an unexpected error.';
        setConnectionState('error');
        setErrorMessage(String(detail));
        setStatusText('Live voice encountered an error.');
      });

      await vapi.start(sessionResponse.data.assistant);
    } catch (error: any) {
      console.error('Failed to initialize Vapi live voice', error);
      setConnectionState('error');
      setErrorMessage(error?.message || 'Live voice could not initialize.');
      setStatusText('Live voice could not initialize.');
    }
  }, [handleVapiMessage, isMuted, selectedAgentId, threadId]);

  const handleToggleMute = useCallback(() => {
    if (!vapiRef.current || connectionState !== 'connected') {
      return;
    }

    const nextMuted = !isMuted;
    vapiRef.current.setMuted(nextMuted);
    setIsMuted(nextMuted);
    setStatusText(nextMuted ? 'Muted' : 'Listening...');
  }, [connectionState, isMuted]);

  const buttonLabel = useMemo(() => {
    if (connectionState === 'connecting') return 'Connecting voice';
    if (connectionState === 'connected') return 'End live voice';
    return 'Start live voice';
  }, [connectionState]);

  return (
    <>
      <Tooltip>
        <TooltipTrigger asChild>
          <Button
            type="button"
            variant="ghost"
            size="sm"
            disabled={disabled}
            onClick={() => setOpen(true)}
            className="h-10 px-2 py-2 bg-transparent border-[1.5px] border-border rounded-2xl text-muted-foreground hover:text-foreground hover:bg-accent/50 flex items-center gap-2 transition-colors"
          >
            <AudioLines className="h-5 w-5" />
          </Button>
        </TooltipTrigger>
        <TooltipContent side="top" className="text-xs">
          <p>Live voice with Mira</p>
        </TooltipContent>
      </Tooltip>

      <Dialog
        open={open}
        onOpenChange={(nextOpen) => {
          setOpen(nextOpen);
          if (!nextOpen && (connectionState === 'connected' || connectionState === 'connecting')) {
            void stopSession();
          }
        }}
      >
        <DialogContent className="sm:max-w-lg">
          <DialogHeader>
            <DialogTitle>Live voice with {activeAgentName}</DialogTitle>
            <DialogDescription>
              Have a real-time conversation in this thread. Final transcript turns are saved back into the conversation so memory can pick them up.
            </DialogDescription>
          </DialogHeader>

          <div className="space-y-4">
            <div className="rounded-2xl border border-border/60 bg-muted/30 p-4">
              <div className="flex items-center justify-between gap-3">
                <div>
                  <p className="text-sm font-medium">Status</p>
                  <p className="text-sm text-muted-foreground">{statusText}</p>
                </div>
                {connectionState === 'connecting' ? (
                  <Loader2 className="h-5 w-5 animate-spin text-muted-foreground" />
                ) : (
                  <div
                    className={`h-3 w-3 rounded-full ${
                      connectionState === 'connected'
                        ? 'bg-emerald-500'
                        : connectionState === 'error'
                          ? 'bg-destructive'
                          : 'bg-muted-foreground/40'
                    }`}
                  />
                )}
              </div>
            </div>

            {errorMessage && (
              <div className="rounded-2xl border border-destructive/30 bg-destructive/5 p-3 text-sm text-destructive">
                {errorMessage}
              </div>
            )}

            <div className="flex flex-wrap items-center gap-2">
              {connectionState === 'connected' ? (
                <>
                  <Button type="button" onClick={() => void stopSession()} className="gap-2">
                    <PhoneOff className="h-4 w-4" />
                    End voice
                  </Button>
                  <Button
                    type="button"
                    variant="outline"
                    onClick={handleToggleMute}
                    className="gap-2"
                  >
                    <MicOff className="h-4 w-4" />
                    {isMuted ? 'Unmute' : 'Mute'}
                  </Button>
                </>
              ) : (
                <Button
                  type="button"
                  onClick={() => void startSession()}
                  disabled={connectionState === 'connecting'}
                  className="gap-2"
                >
                  <PhoneOutgoing className="h-4 w-4" />
                  {buttonLabel}
                </Button>
              )}
            </div>

            <div className="rounded-2xl border border-border/60 bg-background p-4">
              <p className="mb-2 text-sm font-medium">Recent transcript</p>
              {transcriptPreview.length === 0 ? (
                <p className="text-sm text-muted-foreground">
                  Once you start talking, the latest user and assistant turns will show up here.
                </p>
              ) : (
                <div className="space-y-2">
                  {transcriptPreview.map((turn, index) => (
                    <div key={`${turn.role}-${index}`} className="text-sm">
                      <span className="font-medium capitalize">{turn.role}:</span>{' '}
                      <span className="text-muted-foreground">{turn.text}</span>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
        </DialogContent>
      </Dialog>
    </>
  );
});
