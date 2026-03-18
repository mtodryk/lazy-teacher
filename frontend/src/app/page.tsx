'use client';

import { useEffect } from 'react';
import { useAuth } from '@/context/AuthContext';
import { useRouter } from 'next/navigation';

export default function HomePage() {
  const { token } = useAuth();
  const router = useRouter();

  useEffect(() => {
    if (!localStorage.getItem('token')) {
      router.push('/login');
    }
  }, [router]);

  if (!token) return null;

  return (
    <div className="max-w-3xl mx-auto">
      <div className="bg-slate-900 rounded-xl border border-slate-800 p-8 shadow-2xl">
        <h1 className="text-3xl font-bold text-yellow-400 mb-2">Twój panel nauki</h1>
        <p className="text-slate-400 mb-8">Wgraj swoje notatki w formacie PDF, a system wygeneruje dla Ciebie test.</p>
        
        <div className="border-2 border-dashed border-yellow-500/30 rounded-lg p-12 text-center hover:border-yellow-500/60 hover:bg-yellow-500/5 transition-all cursor-pointer group">
          <svg className="mx-auto h-12 w-12 text-yellow-500/50 group-hover:text-yellow-400 mb-4 transition-colors" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
          </svg>
          <h3 className="text-sm font-semibold text-slate-200">Kliknij, aby wybrać plik PDF</h3>
          <p className="text-xs text-slate-500 mt-1 uppercase tracking-widest">Max 50MB</p>
          
          <input type="file" className="hidden" accept=".pdf" id="pdf-upload" />
          <div className="mt-6">
            <label 
              htmlFor="pdf-upload" 
              className="bg-yellow-500 text-slate-950 px-6 py-2 rounded-md hover:bg-yellow-400 cursor-pointer text-sm font-bold inline-block shadow-lg transition-transform active:scale-95"
            >
              Wgraj notatki
            </label>
          </div>
        </div>
      </div>
    </div>
  );
}