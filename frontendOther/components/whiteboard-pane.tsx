'use client';

import { useEffect, useRef, useState } from 'react';

interface WhiteboardPaneProps {
  onDrawingChange?: (data: any) => void;
  isReadOnly?: boolean;
}

export function WhiteboardPane({
  onDrawingChange,
  isReadOnly = false,
}: WhiteboardPaneProps) {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const [isDrawing, setIsDrawing] = useState(false);
  const [context, setContext] = useState<CanvasRenderingContext2D | null>(null);
  const [notes, setNotes] = useState<Array<{ id: string; text: string; x: number; y: number }>>([]);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    const rect = canvas.getBoundingClientRect();
    canvas.width = rect.width;
    canvas.height = rect.height;

    const ctx = canvas.getContext('2d');
    if (ctx) {
      ctx.fillStyle = '#FFFFFF';
      ctx.fillRect(0, 0, canvas.width, canvas.height);
      setContext(ctx);
    }
  }, []);

  const addNote = (text: string, x: number = Math.random() * 300, y: number = Math.random() * 300) => {
    const note = {
      id: `note-${Date.now()}`,
      text,
      x,
      y,
    };
    setNotes((prev) => [...prev, note]);
    drawNote(context, note);
  };

  const drawNote = (ctx: CanvasRenderingContext2D | null, note: any) => {
    if (!ctx) return;

    const width = 200;
    const height = 150;

    // Note background (light yellow)
    ctx.fillStyle = '#FFE5B4';
    ctx.fillRect(note.x, note.y, width, height);

    // Note border
    ctx.strokeStyle = '#D4A574';
    ctx.lineWidth = 2;
    ctx.strokeRect(note.x, note.y, width, height);

    // Text
    ctx.fillStyle = '#111111';
    ctx.font = '14px Inter, system-ui';
    ctx.textBaseline = 'top';

    // Word wrap text
    const words = note.text.split(' ');
    let line = '';
    let y = note.y + 15;
    const lineHeight = 20;
    const maxWidth = width - 20;

    words.forEach((word: string) => {
      const testLine = line + word + ' ';
      const metrics = ctx.measureText(testLine);
      if (metrics.width > maxWidth && line) {
        ctx.fillText(line, note.x + 10, y);
        line = word + ' ';
        y += lineHeight;
      } else {
        line = testLine;
      }
    });
    ctx.fillText(line, note.x + 10, y);
  };

  const addImage = (imageSrc: string, x: number = 50, y: number = 50) => {
    if (!context) return;
    const img = new Image();
    img.crossOrigin = 'anonymous';
    img.src = imageSrc;
    img.onload = () => {
      const width = 300;
      const height = (img.height / img.width) * width;
      context.drawImage(img, x, y, width, height);
    };
  };

  const handleMouseDown = (e: React.MouseEvent) => {
    if (isReadOnly) return;
    setIsDrawing(true);
    const canvas = canvasRef.current;
    if (!canvas || !context) return;
    const rect = canvas.getBoundingClientRect();
    context.beginPath();
    context.moveTo(e.clientX - rect.left, e.clientY - rect.top);
  };

  const handleMouseMove = (e: React.MouseEvent) => {
    if (!isDrawing || !context) return;
    const canvas = canvasRef.current;
    if (!canvas) return;
    const rect = canvas.getBoundingClientRect();
    context.lineTo(e.clientX - rect.left, e.clientY - rect.top);
    context.strokeStyle = '#111111';
    context.lineWidth = 2;
    context.lineCap = 'round';
    context.lineJoin = 'round';
    context.stroke();
  };

  const handleMouseUp = () => {
    setIsDrawing(false);
    if (context) {
      context.closePath();
    }
  };

  const handleClear = () => {
    const canvas = canvasRef.current;
    if (!canvas || !context) return;
    context.fillStyle = '#FFFFFF';
    context.fillRect(0, 0, canvas.width, canvas.height);
    setNotes([]);
  };

  const handleExport = () => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const link = document.createElement('a');
    link.href = canvas.toDataURL('image/png');
    link.download = `whiteboard-${Date.now()}.png`;
    link.click();
  };

  return (
    <div className="flex flex-col h-full bg-secondary">
      <div className="flex items-center justify-between p-6 border-b border-secondary-dark">
        <h2 className="text-2xl font-bold text-primary">Whiteboard</h2>
        <div className="flex gap-3">
          {!isReadOnly && (
            <>
              <button
                onClick={handleClear}
                className="px-4 py-2 text-sm font-medium text-primary bg-secondary-dark rounded-lg hover:bg-primary hover:text-secondary transition-colors"
              >
                Clear
              </button>
              <button
                onClick={handleExport}
                className="px-4 py-2 text-sm font-medium text-secondary bg-primary rounded-lg hover:bg-primary-light transition-colors"
              >
                Export
              </button>
            </>
          )}
        </div>
      </div>

      <canvas
        ref={canvasRef}
        onMouseDown={handleMouseDown}
        onMouseMove={handleMouseMove}
        onMouseUp={handleMouseUp}
        onMouseLeave={handleMouseUp}
        className={`flex-1 bg-white ${!isReadOnly && 'cursor-crosshair'}`}
      />

      <div
        ref={(node) => {
          if (node && !node.dataset.initialized) {
            node.dataset.initialized = 'true';
            (node as any).addNote = addNote;
            (node as any).addImage = addImage;
            (node as any).clear = handleClear;
            (node as any).export = handleExport;
          }
        }}
      />
    </div>
  );
}
