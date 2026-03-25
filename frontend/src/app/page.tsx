'use client';

import { useAuth } from '@/context/AuthContext';
import Link from 'next/link';

export default function HomePage() {
  const { token, username } = useAuth();

  return (
    <div className="max-w-6xl mx-auto px-4 py-12 sm:px-6 lg:px-8">
      {/* Sekcja powitalna */}
      <div className="mb-16 text-center">
        <h1 className="text-4xl md:text-5xl font-black text-yellow-400 mb-4 tracking-tight">
          Witaj{token ? `, ${username}` : ''} w LAZY TEACHER!
        </h1>
        <p className="text-lg text-slate-400 max-w-2xl mx-auto">
          Twój inteligentny asystent nauki. Zamień dowolne notatki w interaktywny quiz i sprawdzaj swoją wiedzę szybciej
          niż kiedykolwiek.
        </p>
      </div>

      {/* Sekcja informacyjna */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-8 mb-16">
        {/* Krok 1 */}
        <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6 shadow-xl relative overflow-hidden group hover:border-yellow-500/30 transition-colors">
          <div className="text-yellow-400 mb-4">
            <svg className="w-10 h-10" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"
              />
            </svg>
          </div>
          <h3 className="text-xl font-bold text-slate-100 mb-2">1. Wgraj materiały</h3>
          <p className="text-slate-400 text-sm">
            Prześlij swoje notatki, wykłady lub rozdziały z podręcznika w formacie PDF.
          </p>
        </div>

        {/* Krok 2 */}
        <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6 shadow-xl relative overflow-hidden group hover:border-yellow-500/30 transition-colors">
          <div className="text-yellow-400 mb-4">
            <svg className="w-10 h-10" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M19.428 15.428a2 2 0 00-1.022-.547l-2.387-.477a6 6 0 00-3.86.517l-.318.158a6 6 0 01-3.86.517L6.05 15.21a2 2 0 00-1.806.547M8 4h8l-1 1v5.172a2 2 0 00.586 1.414l5 5c1.26 1.26.367 3.414-1.415 3.414H4.828c-1.782 0-2.674-2.154-1.414-3.414l5-5A2 2 0 009 10.172V5L8 4z"
              />
            </svg>
          </div>
          <h3 className="text-xl font-bold text-slate-100 mb-2">2. System analizuje</h3>
          <p className="text-slate-400 text-sm">
            Sztuczna inteligencja wyciąga kluczowe informacje z pliku i automatycznie układa pytania.
          </p>
        </div>

        {/* Krok 3 */}
        <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6 shadow-xl relative overflow-hidden group hover:border-yellow-500/30 transition-colors">
          <div className="text-yellow-400 mb-4">
            <svg className="w-10 h-10" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"
              />
            </svg>
          </div>
          <h3 className="text-xl font-bold text-slate-100 mb-2">3. Rozwiąż test</h3>
          <p className="text-slate-400 text-sm">
            Sprawdź się rozwiązując wygenerowany quiz i od razu zobacz, co już umiesz.
          </p>
        </div>
      </div>

      {/* Przycisk akcji */}
      <div className="flex justify-center">
        <Link
          href={token ? '/upload' : '/login'}
          className="bg-yellow-400 text-slate-900 px-10 py-4 rounded-xl hover:bg-yellow-300 text-lg font-black inline-block shadow-[0_0_20px_rgba(250,204,21,0.2)] hover:shadow-[0_0_25px_rgba(250,204,21,0.4)] transition-all active:scale-95 uppercase tracking-wide"
        >
          {token ? 'Przejdź do wgrywania notatek' : 'Przejdź do logowania'}
        </Link>
      </div>
    </div>
  );
}
