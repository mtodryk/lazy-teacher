'use client';

import { useEffect, useState } from 'react';
import { useAuth } from '@/context/AuthContext';
import { useRouter } from 'next/navigation';

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
const MAX_FILE_SIZE = 50 * 1024 * 1024; // 50MB

export default function HomePage() {
  const { token } = useAuth();
  const router = useRouter();
  const [uploadError, setUploadError] = useState('');
  const [uploading, setUploading] = useState(false);
  const [uploadSuccess, setUploadSuccess] = useState('');

  useEffect(() => {
    if (!localStorage.getItem('token')) {
      router.push('/login');
    }
  }, [router]);

  if (!token) return null;

  const handleFileUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    setUploadError('');
    setUploadSuccess('');

    const fileExtension = file.name.split('.').pop()?.toLowerCase();
    if (fileExtension !== 'pdf' || !file.type.includes('pdf')) {
      setUploadError('Dozwolone są tylko pliki PDF.');
      e.target.value = '';
      return;
    }

    if (file.size > MAX_FILE_SIZE) {
      setUploadError('Plik jest zbyt duży. Maksymalny rozmiar to 50MB.');
      e.target.value = '';
      return;
    }

    setUploading(true);
    try {
      const formData = new FormData();
      formData.append('file', file);

      const res = await fetch(`${API_URL}/api/documents/upload/`, {
        method: 'POST',
        headers: { 'Authorization': `Token ${token}` },
        body: formData,
      });

      if (res.ok) {
        setUploadSuccess(`Plik "${file.name}" został przesłany pomyślnie.`);
      } else {
        const data = await res.json().catch((err) => { console.error('Failed to parse upload response:', err); return null; });
        const message = typeof data?.message === 'string' ? data.message : 'Nie udało się przesłać pliku.';
        setUploadError(message);
      }
    } catch (err) {
      console.error('Upload error:', err);
      setUploadError('Błąd połączenia. Sprawdź czy backend działa i spróbuj ponownie.');
    } finally {
      setUploading(false);
      e.target.value = '';
    }
  };

  return (
    <div className="max-w-3xl mx-auto">
      <div className="bg-slate-900 rounded-xl border border-slate-800 p-8 shadow-2xl">
        <h1 className="text-3xl font-bold text-yellow-400 mb-2">Twój panel nauki</h1>
        <p className="text-slate-400 mb-8">Wgraj swoje notatki w formacie PDF, a system wygeneruje dla Ciebie test.</p>

        {uploadError && (
          <div className="bg-red-950/50 border border-red-500/50 text-red-400 p-3 rounded-lg mb-6 text-sm text-center">
            {uploadError}
          </div>
        )}

        {uploadSuccess && (
          <div className="bg-green-950/50 border border-green-500/50 text-green-400 p-3 rounded-lg mb-6 text-sm text-center">
            {uploadSuccess}
          </div>
        )}
        
        <div className="border-2 border-dashed border-yellow-500/30 rounded-lg p-12 text-center hover:border-yellow-500/60 hover:bg-yellow-500/5 transition-all cursor-pointer group">
          <svg className="mx-auto h-12 w-12 text-yellow-500/50 group-hover:text-yellow-400 mb-4 transition-colors" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
          </svg>
          <h3 className="text-sm font-semibold text-slate-200">Kliknij, aby wybrać plik PDF</h3>
          <p className="text-xs text-slate-500 mt-1 uppercase tracking-widest">Max 50MB</p>
          
          <input
            type="file"
            className="hidden"
            accept=".pdf"
            id="pdf-upload"
            onChange={handleFileUpload}
            disabled={uploading}
          />
          <div className="mt-6">
            <label 
              htmlFor="pdf-upload" 
              className={`bg-yellow-500 text-slate-950 px-6 py-2 rounded-md hover:bg-yellow-400 cursor-pointer text-sm font-bold inline-block shadow-lg transition-transform active:scale-95 ${uploading ? 'opacity-60 cursor-not-allowed' : ''}`}
            >
              {uploading ? 'Przesyłanie...' : 'Wgraj notatki'}
            </label>
          </div>
        </div>
      </div>
    </div>
  );
}