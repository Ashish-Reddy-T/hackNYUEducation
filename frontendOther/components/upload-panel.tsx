'use client';

import { useRef, useState } from 'react';
import { useSessionStore } from '@/lib/store/session';

interface UploadPanelProps {
  onUploadStart?: () => void;
  onUploadComplete?: (file: { name: string; type: string }) => void;
}

export function UploadPanel({
  onUploadStart,
  onUploadComplete,
}: UploadPanelProps) {
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [isDragging, setIsDragging] = useState(false);
  const [isUploading, setIsUploading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [error, setError] = useState<string | null>(null);
  const { addMaterial, userId, currentTopic } = useSessionStore();

  const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

  const uploadFile = async (file: File) => {
    if (!file) return;

    const allowedTypes = [
      'application/pdf',
      'text/plain',
      'image/png',
      'image/jpeg',
      'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
    ];

    if (!allowedTypes.includes(file.type)) {
      setError('Unsupported file type. Please upload PDF, TXT, or images.');
      return;
    }

    setIsUploading(true);
    setUploadProgress(0);
    setError(null);
    onUploadStart?.();

    try {
      const formData = new FormData();
      formData.append('file', file);

      formData.append('user_id', userId);
      formData.append('course_id', currentTopic);

      const xhr = new XMLHttpRequest();

      xhr.upload.addEventListener('progress', (e) => {
        if (e.lengthComputable) {
          const percentComplete = (e.loaded / e.total) * 100;
          setUploadProgress(percentComplete);
        }
      });

      xhr.addEventListener('load', () => {
        if (xhr.status === 200) {
          console.log('[Agora] File uploaded successfully');
          addMaterial(file.name, file.type);
          setUploadProgress(100);
          onUploadComplete?.({ name: file.name, type: file.type });

          // Reset after brief delay
          setTimeout(() => {
            setIsUploading(false);
            setUploadProgress(0);
          }, 1000);
        } else {
          setError('Upload failed. Please try again.');
          setIsUploading(false);
        }
      });

      xhr.addEventListener('error', () => {
        setError('Upload error. Please check your connection.');
        setIsUploading(false);
      });

      xhr.open('POST', `${apiUrl}/api/materials/upload`);
      xhr.send(formData);
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Upload failed';
      setError(message);
      setIsUploading(false);
    }
  };

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(true);
  };

  const handleDragLeave = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(false);
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(false);

    const files = e.dataTransfer.files;
    if (files.length > 0) {
      uploadFile(files[0]);
    }
  };

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = e.currentTarget.files;
    if (files && files.length > 0) {
      uploadFile(files[0]);
    }
  };

  return (
    <div className="flex flex-col h-full bg-secondary">
      <div className="flex-shrink-0 px-6 py-4 border-b border-secondary-dark">
        <h3 className="text-lg font-bold text-primary">Materials</h3>
        <p className="text-xs text-primary-light mt-1">
          Upload PDFs, notes, or images to study
        </p>
      </div>

      <div
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
        onClick={() => fileInputRef.current?.click()}
        className={`flex-1 mx-4 my-6 rounded-lg border-2 border-dashed transition-all cursor-pointer
          flex flex-col items-center justify-center
          ${
            isDragging
              ? 'border-accent bg-accent bg-opacity-5'
              : 'border-secondary-dark hover:border-primary hover:bg-secondary-dark'
          }
          ${isUploading ? 'opacity-50' : ''}
        `}
      >
        <input
          ref={fileInputRef}
          type="file"
          onChange={handleFileSelect}
          disabled={isUploading}
          className="hidden"
          accept=".pdf,.txt,.png,.jpg,.jpeg,.docx"
        />

        <div className="text-center">
          <svg
            className="w-12 h-12 mx-auto mb-3 text-primary-light"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={1.5}
              d="M12 4v16m8-8H4"
            />
          </svg>
          <p className="text-sm font-semibold text-primary">
            {isUploading ? 'Uploading...' : 'Drag files here or click'}
          </p>
          <p className="text-xs text-primary-light mt-1">
            PDF, TXT, PNG, JPG, DOCX
          </p>
        </div>

        {isUploading && uploadProgress > 0 && (
          <div className="absolute bottom-4 left-4 right-4 bg-secondary-dark rounded-full overflow-hidden h-2">
            <div
              className="bg-accent h-full transition-all duration-300"
              style={{ width: `${uploadProgress}%` }}
            />
          </div>
        )}
      </div>

      {error && (
        <div className="mx-4 mb-4 p-3 bg-red-50 border border-red-200 rounded-lg">
          <p className="text-sm text-red-700">{error}</p>
        </div>
      )}

      <div className="flex-shrink-0 px-6 pb-6 border-t border-secondary-dark max-h-48 overflow-y-auto">
        <p className="text-xs font-semibold text-primary-light uppercase tracking-wide mb-3">
          Recent Materials
        </p>
        <div className="space-y-2">
          <MaterialsList />
        </div>
      </div>
    </div>
  );
}

function MaterialsList() {
  const { uploadedMaterials } = useSessionStore();

  if (uploadedMaterials.length === 0) {
    return (
      <p className="text-xs text-primary-light italic">
        No materials uploaded yet
      </p>
    );
  }

  return (
    <>
      {uploadedMaterials.map((material) => (
        <div
          key={material.id}
          className="flex items-center justify-between p-2 bg-secondary-dark rounded hover:bg-primary hover:bg-opacity-5 transition-colors"
        >
          <div className="flex items-center gap-2 flex-1 min-w-0">
            <FileIcon type={material.type} />
            <span className="text-xs text-primary truncate font-medium">
              {material.name}
            </span>
          </div>
          <button
            onClick={() => {}}
            className="text-xs text-primary-light hover:text-accent transition-colors"
            title="Remove material"
          >
            ✕
          </button>
        </div>
      ))}
    </>
  );
}

function FileIcon({ type }: { type: string }) {
  if (type === 'application/pdf') {
    return <span className="text-red-500 font-bold text-sm">PDF</span>;
  }
  if (type.startsWith('image/')) {
    return <span className="text-blue-500 font-bold text-sm">IMG</span>;
  }
  return <span className="text-gray-500 font-bold text-sm">FILE</span>;
}
