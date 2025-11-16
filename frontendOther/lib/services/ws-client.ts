import { io, Socket } from 'socket.io-client';

interface WSClientConfig {
  url: string;
  userId: string;
  sessionId: string;
}

type MessageCallback = (message: any) => void;

export class WSClient {
  private socket: Socket | null = null;
  private config: WSClientConfig | null = null;
  private callbacks: Map<string, MessageCallback[]> = new Map();
  private reconnectAttempts = 0;
  private maxReconnectAttempts = 5;

  async connect(config: WSClientConfig): Promise<void> {
    this.config = config;

    return new Promise((resolve, reject) => {
      try {
        this.socket = io(config.url, {
          reconnection: true,
          reconnectionDelay: 1000,
          reconnectionDelayMax: 5000,
          reconnectionAttempts: this.maxReconnectAttempts,
          query: {
            user_id: config.userId,
            session_id: config.sessionId,
          },
        });

        this.socket.on('connect', () => {
          console.log('[Agora] WebSocket connected');
          this.reconnectAttempts = 0;
          this.emit('connection_status', { connected: true });
          resolve();
        });

        this.socket.on('disconnect', () => {
          console.log('[Agora] WebSocket disconnected');
          this.emit('connection_status', { connected: false });
        });

        this.socket.on('error', (error) => {
          console.error('[Agora] WebSocket error:', error);
          this.emit('error', { message: error });
        });

        this.socket.on('transcript', (data) => {
          this.emit('transcript', data);
        });

        this.socket.on('audio_response', (data) => {
          this.emit('audio_response', data);
        });

        this.socket.on('visual', (data) => {
          this.emit('visual', data);
        });

        this.socket.on('session_status', (data) => {
          this.emit('session_status', data);
        });

        // Timeout for connection
        const timeout = setTimeout(() => {
          reject(new Error('WebSocket connection timeout'));
        }, 10000);

        this.socket.once('connect', () => {
          clearTimeout(timeout);
        });
      } catch (error) {
        reject(error);
      }
    });
  }

  disconnect(): void {
    if (this.socket) {
      this.socket.disconnect();
      this.socket = null;
    }
  }

  async sendAudio(blob: Blob): Promise<void> {
    if (!this.socket || !this.config) {
      throw new Error('WebSocket not connected');
    }

    try {
      const base64 = await this.blobToBase64(blob);
      this.socket.emit('audio', {
        type: 'audio',
        session_id: this.config.sessionId,
        user_id: this.config.userId,
        format: 'audio/webm',
        data: base64,
      });
    } catch (error) {
      console.error('[Agora] Failed to send audio:', error);
      throw error;
    }
  }

  sendText(text: string): void {
    if (!this.socket || !this.config) {
      throw new Error('WebSocket not connected');
    }

    this.socket.emit('text', {
      type: 'text',
      session_id: this.config.sessionId,
      user_id: this.config.userId,
      text,
    });
  }

  on(messageType: string, callback: MessageCallback): void {
    if (!this.callbacks.has(messageType)) {
      this.callbacks.set(messageType, []);
    }
    this.callbacks.get(messageType)?.push(callback);
  }

  off(messageType: string, callback: MessageCallback): void {
    const callbacks = this.callbacks.get(messageType);
    if (callbacks) {
      const index = callbacks.indexOf(callback);
      if (index > -1) {
        callbacks.splice(index, 1);
      }
    }
  }

  private emit(messageType: string, data: any): void {
    const callbacks = this.callbacks.get(messageType);
    if (callbacks) {
      callbacks.forEach((cb) => cb(data));
    }
  }

  private blobToBase64(blob: Blob): Promise<string> {
    return new Promise((resolve, reject) => {
      const reader = new FileReader();
      reader.onloadend = () => {
        const base64 = reader.result as string;
        resolve(base64.split(',')[1]);
      };
      reader.onerror = reject;
      reader.readAsDataURL(blob);
    });
  }

  isConnected(): boolean {
    return this.socket?.connected ?? false;
  }
}

export const wsClient = new WSClient();
