'use client';

import { useEffect, useRef } from 'react';

export interface Message {
  id: string;
  from: 'student' | 'tutor';
  text: string;
  timestamp: Date;
}

interface TranscriptPanelProps {
  messages: Message[];
  isLoading?: boolean;
  onScroll?: (position: number) => void;
}

export function TranscriptPanel({
  messages,
  isLoading = false,
  onScroll,
}: TranscriptPanelProps) {
  const scrollContainerRef = useRef<HTMLDivElement>(null);
  const endRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const handleScroll = () => {
    if (scrollContainerRef.current && onScroll) {
      onScroll(scrollContainerRef.current.scrollTop);
    }
  };

  return (
    <div className="flex flex-col h-full bg-secondary border-l border-secondary-dark">
      <div className="flex-shrink-0 px-6 py-4 border-b border-secondary-dark">
        <h3 className="text-lg font-bold text-primary">Conversation</h3>
        <p className="text-xs text-primary-light mt-1">
          {messages.length} messages
        </p>
      </div>

      <div
        ref={scrollContainerRef}
        onScroll={handleScroll}
        className="flex-1 overflow-y-auto p-6 space-y-4"
      >
        {messages.length === 0 ? (
          <div className="flex items-center justify-center h-full text-center">
            <div>
              <p className="text-primary-light font-medium">No messages yet</p>
              <p className="text-xs text-primary-light mt-2">
                Hold the button and speak to get started
              </p>
            </div>
          </div>
        ) : (
          messages.map((msg) => (
            <div
              key={msg.id}
              className={`flex ${
                msg.from === 'student' ? 'justify-end' : 'justify-start'
              } animate-fade-in`}
            >
              <div
                className={`max-w-xs px-4 py-3 rounded-lg ${
                  msg.from === 'student'
                    ? 'bg-accent text-white rounded-br-none'
                    : 'bg-secondary-dark text-primary rounded-bl-none'
                }`}
              >
                <p className="text-sm leading-relaxed">{msg.text}</p>
                <p
                  className={`text-xs mt-2 ${
                    msg.from === 'student'
                      ? 'text-white text-opacity-70'
                      : 'text-primary-light'
                  }`}
                >
                  {msg.timestamp.toLocaleTimeString([], {
                    hour: '2-digit',
                    minute: '2-digit',
                  })}
                </p>
              </div>
            </div>
          ))
        )}

        {isLoading && (
          <div className="flex justify-start">
            <div className="bg-secondary-dark text-primary px-4 py-3 rounded-lg rounded-bl-none">
              <div className="flex gap-2 items-center">
                <div className="w-2 h-2 bg-accent rounded-full animate-pulse" />
                <div className="w-2 h-2 bg-accent rounded-full animate-pulse animation-delay-200" />
                <div className="w-2 h-2 bg-accent rounded-full animate-pulse animation-delay-400" />
              </div>
            </div>
          </div>
        )}

        <div ref={endRef} />
      </div>

      <div className="flex-shrink-0 px-6 py-3 border-t border-secondary-dark bg-secondary-dark text-xs text-primary-light text-center">
        Messages are transcribed in real-time
      </div>
    </div>
  );
}
