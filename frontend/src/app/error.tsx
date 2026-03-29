'use client';

import { useEffect } from 'react';
import Link from 'next/link';

export default function Error({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  useEffect(() => {
    // Możesz tutaj dodać logowanie błędu do zewnętrznego systemu
    console.error(error);
  }, [error]);

  return (
    <div className="min-h-[80vh] flex flex-col items-center justify-center px-4 text-center">
      <div className="w-24 h-24 bg-red-500/10 rounded-full flex items-center justify-center mb-8 border border-red-500/20">
        <svg className="w-12 h-12 text-red-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2.5" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
        </svg>
      </div>

      <h1 className="text-5xl md:text-7xl font-black text-white uppercase italic tracking-tighter mb-4">
        Coś pękło...
      </h1>
      
      <p className="max-w-md text-zinc-500 text-lg font-medium mb-12 leading-relaxed">
        Wystąpił krytyczny błąd systemu. Wygląda na to, że serwer potrzebuje przerwy kawowej.
      </p>

      <div className="flex flex-col sm:flex-row gap-4">
        <button
          onClick={() => reset()}
          className="px-10 py-5 bg-white text-black font-black rounded-2xl uppercase tracking-widest text-sm transition-all hover:bg-zinc-200 active:scale-95"
        >
          Spróbuj ponownie
        </button>
        
        <Link 
          href="/"
          className="px-10 py-5 bg-zinc-900 text-zinc-400 border border-zinc-800 font-black rounded-2xl uppercase tracking-widest text-sm transition-all hover:text-white hover:border-zinc-700 active:scale-95"
        >
          Strona główna
        </Link>
      </div>

      {process.env.NODE_ENV === 'development' && (
        <div className="mt-12 p-4 bg-zinc-950 border border-zinc-800 rounded-xl text-left max-w-2xl overflow-auto shadow-inner">
          <p className="text-red-400 font-mono text-xs uppercase mb-2 font-bold tracking-widest">Debug Info:</p>
          <pre className="text-zinc-600 font-mono text-[10px] whitespace-pre-wrap">
            {error.message || "Unknown Error"}
            {error.digest && `\nDigest: ${error.digest}`}
          </pre>
        </div>
      )}
    </div>
  );
}