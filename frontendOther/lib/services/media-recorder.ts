export class AudioRecorder {
  private mediaRecorder: MediaRecorder | null = null;
  private stream: MediaStream | null = null;
  private chunks: Blob[] = [];

  async initialize(): Promise<void> {
    try {
      this.stream = await navigator.mediaDevices.getUserMedia({
        audio: {
          echoCancellation: true,
          noiseSuppression: true,
          autoGainControl: true,
        },
      });

      this.mediaRecorder = new MediaRecorder(this.stream, {
        mimeType: 'audio/webm',
      });

      this.mediaRecorder.ondataavailable = (event) => {
        if (event.data.size > 0) {
          this.chunks.push(event.data);
        }
      };
    } catch (error) {
      console.error('[Agora] Failed to initialize audio recorder:', error);
      throw error;
    }
  }

  start(): void {
    if (!this.mediaRecorder) throw new Error('Recorder not initialized');
    this.chunks = [];
    this.mediaRecorder.start();
  }

  stop(): Blob {
    if (!this.mediaRecorder) throw new Error('Recorder not initialized');
    this.mediaRecorder.stop();
    return new Blob(this.chunks, { type: 'audio/webm' });
  }

  async getAudioContext(): Promise<AudioContext> {
    const audioContext = new (window.AudioContext || (window as any).webkitAudioContext)();
    if (this.stream) {
      const analyser = audioContext.createAnalyser();
      const source = audioContext.createMediaStreamAudioSource(this.stream);
      source.connect(analyser);
    }
    return audioContext;
  }

  cleanup(): void {
    if (this.stream) {
      this.stream.getTracks().forEach((track) => track.stop());
    }
  }
}
