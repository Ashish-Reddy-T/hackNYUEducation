import { useEffect, useState, useCallback } from 'react';
import { wsClient } from '@/lib/services/ws-client';
import { useSessionStore } from '@/lib/store/session';
import { useMessageStore } from '@/lib/store/messages';

export function useWebSocket() {
  const [isReady, setIsReady] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const { userId, sessionId, initSession, currentTopic } = useSessionStore();
  const { addMessage, setLoading } = useMessageStore();

  useEffect(() => {
    const setupConnection = async () => {
      try {
        // Socket.IO automatically uses /socket.io path, so just use base URL
        const wsUrl = process.env.NEXT_PUBLIC_WS_URL || 'http://localhost:8000';
        
        console.log('[Agora] Connecting to WebSocket:', wsUrl);
        
        // Setup connect handler BEFORE connecting
        wsClient.on('connect', () => {
          console.log('[Agora] Socket.IO connected! Socket ID:', wsClient.isConnected());
          
          // 3. FIX THIS BLOCK
          console.log('[Agora] Sending init_session...');
          wsClient.send('init_session', {
            user_id: userId,
            session_id: sessionId,
            course_id: currentTopic || 'General' // <-- Use the topic from the store
          });
        });
        
        await wsClient.connect({
          url: wsUrl,
          userId,
          sessionId,
        });

        wsClient.on('session_initialized', (data) => {
          console.log('[Agora] Session initialized:', data);
          setIsReady(true);
        });

        wsClient.on('transcript', (data) => {
          console.log('[Agora] Transcript received:', data);
          addMessage(data.from, data.text);
          setLoading(false);
        });

        wsClient.on('audio_response', (data) => {
          console.log('[Agora] Audio response received');
          
          if (useSessionStore.getState().isTutorAudioEnabled) {
            const audioData = `data:${data.format};base64,${data.data}`;
            const audio = new Audio(audioData);
            audio.play().catch((err) => {
              console.error('[Agora] Audio playback failed:', err);
            });
          } else {
            console.log('[Agora] Audio playback skipped (tutor is muted)');
          }
        });

        wsClient.on('visual', (data) => {
          console.log('[Agora] Visual action received:', data);
          // Emit visual action event
          window.dispatchEvent(
            new CustomEvent('agora:visual', { detail: data })
          );
        });

        wsClient.on('session_status', (data) => {
          console.log('[Agora] Session status:', data);
          if (data.status === 'complete') {
            setLoading(false);
          }
        });

        wsClient.on('connection_status', (data) => {
          console.log('[Agora] Connection status:', data);
          setIsReady(data.connected);
        });

        wsClient.on('error', (data) => {
          setError(data.message);
          console.error('[Agora] WebSocket error:', data);
          setLoading(false);
          setIsReady(false);
        });

        // Don't set ready until connection is established
        // isReady will be set by connection_status event
      } catch (err) {
        const message = err instanceof Error ? err.message : 'Connection failed';
        setError(message);
        console.error('[Agora] WebSocket setup failed:', err);
        setIsReady(false);
      }
    };

    if (userId && sessionId) {
      setupConnection();
    }

    return () => {
      wsClient.disconnect();
    };
  }, [userId, sessionId, addMessage, setLoading, initSession, currentTopic]);

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
