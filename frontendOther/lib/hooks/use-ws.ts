import { useEffect, useState, useCallback } from 'react';
import { wsClient } from '@/lib/services/ws-client';
import { useSessionStore } from '@/lib/store/session';
import { useMessageStore } from '@/lib/store/messages';

export function useWebSocket() {
  const [isReady, setIsReady] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const { userId, sessionId, initSession } = useSessionStore();
  const { addMessage, setLoading } = useMessageStore();

  useEffect(() => {
    const setupConnection = async () => {
      try {
        const wsUrl = process.env.NEXT_PUBLIC_WS_URL || 'http://localhost:8000';
        
        await wsClient.connect({
          url: wsUrl,
          userId,
          sessionId,
        });

        wsClient.on('transcript', (data) => {
          addMessage(data.from, data.text);
          setLoading(false);
        });

        wsClient.on('audio_response', (data) => {
          // Handle audio playback
          const audioData = `data:audio/mpeg;base64,${data.data}`;
          const audio = new Audio(audioData);
          audio.play().catch((err) => {
            console.error('[Agora] Audio playback failed:', err);
          });
        });

        wsClient.on('visual', (data) => {
          // Emit visual action event
          window.dispatchEvent(
            new CustomEvent('agora:visual', { detail: data })
          );
        });

        wsClient.on('connection_status', (data) => {
          setIsReady(data.connected);
        });

        wsClient.on('error', (data) => {
          setError(data.message);
          console.error('[Agora] WebSocket error:', data);
        });

        setIsReady(true);
      } catch (err) {
        const message = err instanceof Error ? err.message : 'Connection failed';
        setError(message);
        console.error('[Agora] WebSocket setup failed:', err);
      }
    };

    setupConnection();

    return () => {
      wsClient.disconnect();
    };
  }, [userId, sessionId, addMessage, setLoading]);

  const sendAudio = useCallback(
    async (blob: Blob) => {
      if (!isReady) {
        setError('WebSocket not ready');
        return;
      }

      try {
        setLoading(true);
        await wsClient.sendAudio(blob);
      } catch (err) {
        const message = err instanceof Error ? err.message : 'Failed to send audio';
        setError(message);
        setLoading(false);
      }
    },
    [isReady, setLoading]
  );

  const sendText = useCallback(
    (text: string) => {
      if (!isReady) {
        setError('WebSocket not ready');
        return;
      }

      try {
        wsClient.sendText(text);
      } catch (err) {
        const message = err instanceof Error ? err.message : 'Failed to send text';
        setError(message);
      }
    },
    [isReady]
  );

  return {
    isReady,
    error,
    sendAudio,
    sendText,
    isConnected: wsClient.isConnected(),
  };
}
