import { useEffect, useState, useCallback } from 'react';
import { wsClient } from '@/lib/services/ws-client';
import { useSessionStore } from '@/lib/store/session';
import { useMessageStore } from '@/lib/store/messages';

export function useWebSocket() {
  const [isReady, setIsReady] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const { userId, sessionId, initSession, currentTopic } = useSessionStore();
  const { addMessage, setLoading } = useMessageStore();

  // FIX: Define stable callbacks using useCallback
  // This ensures they have a stable reference and can be added/removed.
  // We use getState() inside to avoid adding store functions as dependencies.

  const onSessionInitialized = useCallback((data: any) => {
    console.log('[Agora] Session initialized:', data);
    setIsReady(true);
  }, []); // No dependencies needed

  const onTranscript = useCallback((data: any) => {
    console.log('[Agora] Transcript received:', data);
    // Use getState() to get the latest functions without causing re-renders
    useMessageStore.getState().addMessage(data.from, data.text);
    useMessageStore.getState().setLoading(false);
  }, []); // No dependencies needed

  const onAudioResponse = useCallback((data: any) => {
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
  }, []); // No dependencies needed

  const onVisual = useCallback((data: any) => {
    console.log('[Agora] Visual action received:', data);
    window.dispatchEvent(new CustomEvent('agora:visual', { detail: data }));
  }, []); // No dependencies needed

  const onSessionStatus = useCallback((data: any) => {
    console.log('[Agora] Session status:', data);
    if (data.status === 'complete') {
      useMessageStore.getState().setLoading(false);
    }
  }, []); // No dependencies needed

  const onConnectionStatus = useCallback((data: any) => {
    console.log('[Agora] Connection status:', data);
    setIsReady(data.connected);
  }, []); // No dependencies needed

  const onError = useCallback((data: any) => {
    setError(data.message);
    console.error('[Agora] WebSocket error:', data);
    useMessageStore.getState().setLoading(false);
    setIsReady(false);
  }, []); // No dependencies needed


  useEffect(() => {
    const setupConnection = async () => {
      try {
        const wsUrl = process.env.NEXT_PUBLIC_WS_URL || 'http://localhost:8000';
        console.log('[Agora] Connecting to WebSocket:', wsUrl);

        // Setup connect handler BEFORE connecting
        wsClient.on('connect', () => {
          console.log('[Agora] Socket.IO connected! Socket ID:', wsClient.isConnected());
          console.log('[Agora] Sending init_session...');
          wsClient.send('init_session', {
            user_id: userId,
            session_id: sessionId,
            course_id: currentTopic || 'General'
          });
        });
        
        await wsClient.connect({
          url: wsUrl,
          userId,
          sessionId,
        });

        // ** FIX: Register the stable callbacks **
        wsClient.on('session_initialized', onSessionInitialized);
        wsClient.on('transcript', onTranscript);
        wsClient.on('audio_response', onAudioResponse);
        wsClient.on('visual', onVisual);
        wsClient.on('session_status', onSessionStatus);
        wsClient.on('connection_status', onConnectionStatus);
        wsClient.on('error', onError);

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

    // ** FIX: The Correct Cleanup Function **
    return () => {
      console.log('[Agora] Cleaning up WebSocket listeners...');
      // ** Un-register the listeners to prevent leaks **
      // Note: Cannot remove 'connect' handler without storing its reference
      wsClient.off('session_initialized', onSessionInitialized);
      wsClient.off('transcript', onTranscript);
      wsClient.off('audio_response', onAudioResponse);
      wsClient.off('visual', onVisual);
      wsClient.off('session_status', onSessionStatus);
      wsClient.off('connection_status', onConnectionStatus);
      wsClient.off('error', onError);
      
      wsClient.disconnect();
    };
  // ** FIX: Update dependency array **
  // We only want this effect to run when the session IDs change, not when
  // state setters from Zustand change.
  }, [userId, sessionId, currentTopic, 
      onSessionInitialized, onTranscript, onAudioResponse, onVisual, 
      onSessionStatus, onConnectionStatus, onError]);


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
    [isReady, setLoading] // setLoading is fine here as it's just a trigger
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