'use client';

import { useEffect, useState, useRef } from 'react';
import { useAuth } from '@/context/AuthContext';
import { useRouter } from 'next/navigation';

export default function UploadPage() {
  const { token, logout } = useAuth();
  const router = useRouter();

  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [isUploading, setIsUploading] = useState(false);
  const [uploadStatus, setUploadStatus] = useState<{ type: 'success' | 'error' | null; message: string }>({
    type: null,
    message: ''
  });

  const fileInputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    if (!localStorage.getItem('token')) {
      router.push('/login');
    }
  }, [router]);

  if (!token) return null;

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      if (file.type !== 'application/pdf') {
        setUploadStatus({ type: 'error', message: 'Proszę wybrać plik w formacie PDF.' });
        setSelectedFile(null);
        return;
      }
      setSelectedFile(file);
      setUploadStatus({ type: null, message: '' });
    }
  };

  const handleUpload = async () => {
    if (!selectedFile) return;

    setIsUploading(true);
    setUploadStatus({ type: null, message: '' });

    const formData = new FormData();
    formData.append('file', selectedFile);

    // Czyszczenie tokenu z ewentualnych cudzysłowów i białych znaków:
    const cleanToken = token ? token.replace(/['"]+/g, '').trim() : '';

    // Zobaczmy w konsoli, jak DOKŁADNIE wygląda token
    console.log('Czysty token do wysyłki to:', cleanToken);

    try {
      const response = await fetch('http://localhost:8000/api/documents/upload/', {
        method: 'POST',
        headers: { Authorization: `Token ${cleanToken}` },
        body: formData
      });

      if (response.status === 401) {
        logout();
        return;
      }
      if (!response.ok) {
        throw new Error('Błąd podczas wgrywania pliku.');
      }

      const data = await response.json();

      // Sukces! Przekierowujemy od razu na stronę analizy dokumentu
      router.push(`/document/${data.document_id}`);
    } catch (error) {
      console.error(error);
      setUploadStatus({ type: 'error', message: 'Nie udało się wgrać pliku. Spróbuj ponownie.' });
    } finally {
      setIsUploading(false);
    }
  };

  return (
    <div className="max-w-3xl mx-auto px-4 py-12">
      <div className="bg-slate-900 rounded-xl border border-slate-800 p-8 shadow-2xl">
        <h1 className="text-3xl font-bold text-yellow-400 mb-2">Wgraj nowe materiały</h1>
        <p className="text-slate-400 mb-8">
          Wgraj swoje notatki w formacie PDF, a LazyTeacher wygeneruje dla Ciebie quiz.
        </p>

        <div
          onClick={() => fileInputRef.current?.click()}
          className={`border-2 border-dashed rounded-lg p-12 text-center transition-all cursor-pointer group
            ${selectedFile ? 'border-green-500/50 bg-green-500/5' : 'border-yellow-500/30 hover:border-yellow-500/60 hover:bg-yellow-500/5'}
          `}
        >
          <svg
            className={`mx-auto h-12 w-12 mb-4 transition-colors ${selectedFile ? 'text-green-500' : 'text-yellow-500/50 group-hover:text-yellow-400'}`}
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
          >
            {selectedFile ? (
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"
              />
            ) : (
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12"
              />
            )}
          </svg>

          <h3 className="text-sm font-semibold text-slate-200">
            {selectedFile ? selectedFile.name : 'Kliknij, aby wybrać plik PDF'}
          </h3>
          <p className="text-xs text-slate-500 mt-1 uppercase tracking-widest">
            {selectedFile ? `${(selectedFile.size / (1024 * 1024)).toFixed(2)} MB` : 'Max 50MB'}
          </p>

          <input type="file" className="hidden" accept=".pdf" ref={fileInputRef} onChange={handleFileChange} />
        </div>

        {uploadStatus.message && (
          <div
            className={`mt-6 p-4 rounded-md text-sm font-medium ${uploadStatus.type === 'success' ? 'bg-green-500/10 text-green-400 border border-green-500/20' : 'bg-red-500/10 text-red-400 border border-red-500/20'}`}
          >
            {uploadStatus.message}
          </div>
        )}

        {/* Tutaj zmieniłem justify-end na justify-center */}
        <div className="mt-8 flex justify-center">
          <button
            onClick={handleUpload}
            disabled={!selectedFile || isUploading}
            className={`px-8 py-3 rounded-lg text-sm font-black inline-block shadow-lg transition-all uppercase tracking-wide
              ${
                !selectedFile || isUploading
                  ? 'bg-slate-800 text-slate-500 cursor-not-allowed'
                  : 'bg-yellow-500 text-slate-950 hover:bg-yellow-400 active:scale-95 shadow-[0_0_15px_rgba(250,204,21,0.2)]'
              }
            `}
          >
            {isUploading ? 'Wgrywanie...' : 'Wyślij do analizy'}
          </button>
        </div>
      </div>
    </div>
  );
}
