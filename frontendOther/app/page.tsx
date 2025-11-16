'use client';

import { useEffect, useRef, useState } from 'react';
import { OrbStatus } from '@/components/orb-status';
import { RecorderButton } from '@/components/recorder-button';
import { TranscriptPanel } from '@/components/transcript-panel';
import { WhiteboardPane } from '@/components/whiteboard-pane';
import { SessionSidebar } from '@/components/session-sidebar';
import { useWebSocket } from '@/lib/hooks/use-ws';
import { useMessageStore } from '@/lib/store/messages';
import { useSessionStore } from '@/lib/store/session';

type OrbState = 'idle' | 'listening' | 'thinking' | 'speaking';

export default function AgoraPage() {
  const whiteboardRef = useRef<any>(null);
  const [orbState, setOrbState] = useState<OrbState>('idle');
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false);
  const [textInput, setTextInput] = useState('');
  const { isReady, sendAudio, sendText, isConnected } = useWebSocket();
  const { messages, isLoading, addMessage } = useMessageStore();
  const { initSession } = useSessionStore();

  useEffect(() => {
    initSession();
  }, [initSession]);

  useEffect(() => {
    const handleVisualAction = (event: Event) => {
      const customEvent = event as CustomEvent;
      const action = customEvent.detail;

      if (whiteboardRef.current) {
        switch (action.action) {
          case 'CREATE_NOTE':
            whiteboardRef.current.addNote?.(
              action.payload.text,
              action.payload.x,
              action.payload.y
            );
            break;
          case 'LOAD_IMAGE':
            whiteboardRef.current.addImage?.(
              action.payload.imageSrc,
              action.payload.x,
              action.payload.y
            );
            break;
          case 'CLEAR_BOARD':
            whiteboardRef.current.clear?.();
            break;
        }
      }
    };

    window.addEventListener('agora:visual', handleVisualAction);
    return () => window.removeEventListener('agora:visual', handleVisualAction);
  }, []);

  const handleAudioSubmit = async (blob: Blob) => {
    if (!isReady) {
      console.error('[Agora] WebSocket not ready');
      return;
    }

    try {
      setOrbState('thinking');
      addMessage('student', 'Recording...');
      await sendAudio(blob);
    } catch (error) {
      console.error('[Agora] Failed to send audio:', error);
      setOrbState('idle');
    }
  };

  const handleTextSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!isReady || !textInput.trim()) {
      return;
    }

    try {
      setOrbState('thinking');
      addMessage('student', textInput);
      await sendText(textInput);
      setTextInput('');
    } catch (error) {
      console.error('[Agora] Failed to send text:', error);
      setOrbState('idle');
    }
  };

  useEffect(() => {
    if (isLoading) {
      setOrbState('thinking');
    } else {
      setOrbState('idle');
    }
  }, [isLoading]);

  return (
    <main className="flex h-screen w-full bg-secondary overflow-hidden">
      <div className="flex-1 flex flex-col">
        <header className="flex-shrink-0 px-8 py-6 border-b border-secondary-dark bg-secondary">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-4xl font-bold text-primary">Agora</h1>
              <p className="text-sm text-primary-light mt-1">
                {isConnected ? 'Connected' : 'Connecting...'}
              </p>
            </div>
            <div className="flex items-center gap-4">
              <span
                className={`text-xs font-semibold uppercase tracking-widest px-3 py-1 rounded-full ${
                  isConnected
                    ? 'bg-green-100 text-green-700'
                    : 'bg-yellow-100 text-yellow-700'
                }`}
              >
                {isConnected ? 'Ready' : 'Connecting'}
              </span>
            </div>
          </div>
        </header>

        <div className="flex-1 flex overflow-hidden min-h-0">
          <div className="flex-1 flex flex-col min-w-0 min-h-0">
            <WhiteboardPane ref={whiteboardRef} />
          </div>

          <div className="w-96 flex flex-col border-l border-secondary-dark flex-shrink-0">
            <TranscriptPanel messages={messages} isLoading={isLoading} />
          </div>
        </div>

        <div className="flex-shrink-0 flex flex-col items-center justify-center py-8 px-6 bg-secondary border-t border-secondary-dark gap-6">
          <OrbStatus state={orbState} />

          <RecorderButton
            onAudioSubmit={handleAudioSubmit}
            disabled={!isReady}
            isProcessing={isLoading}
          />

          <form onSubmit={handleTextSubmit} className="w-full max-w-2xl flex gap-2">
            <input
              type="text"
              value={textInput}
              onChange={(e) => setTextInput(e.target.value)}
              placeholder="Or type your question here..."
              disabled={!isReady || isLoading}
              className="flex-1 px-4 py-2 rounded-lg border border-secondary-dark bg-secondary-light text-primary placeholder:text-primary-light/50 disabled:opacity-50 disabled:cursor-not-allowed focus:outline-none focus:ring-2 focus:ring-primary/50 focus:border-primary"
              autoComplete="off"
            />
            <button
              type="submit"
              disabled={!isReady || isLoading || !textInput.trim()}
              className="px-6 py-2 rounded-lg bg-primary text-white font-medium hover:bg-primary-dark disabled:opacity-50 disabled:cursor-not-allowed transition-colors focus:outline-none focus:ring-2 focus:ring-primary/50"
            >
              Send
            </button>
          </form>

          <p className="text-xs text-primary-light text-center max-w-xs">
            {orbState === 'idle' && 'Hold the button and speak, or type your question'}
            {orbState === 'listening' && 'Listening to your question...'}
            {orbState === 'thinking' && 'Tutor is thinking...'}
            {orbState === 'speaking' && 'Tutor is responding...'}
          </p>
        </div>
      </div>

      <SessionSidebar
        isCollapsed={sidebarCollapsed}
        onToggle={setSidebarCollapsed}
      />
    </main>
  );
}
