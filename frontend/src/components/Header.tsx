'use client';

import Link from 'next/link';
import { useAuth } from '@/context/AuthContext';

export default function Header() {
  const { token, username, logout } = useAuth();

  return (
    <header className="fixed top-0 left-0 w-full z-50 bg-zinc-900 border-b border-zinc-800 text-zinc-100 shadow-xl">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between items-center h-20 relative">
          
          {/* Pusta sekcja po lewej stronie, aby poprawnie wyrównać układ flex */}
          <div className="flex-1"></div>

          {/* Idealnie wyśrodkowana i mocno powiększona nazwa */}
          <Link 
            href="/" 
            className="absolute left-1/2 -translate-x-1/2 text-4xl sm:text-5xl font-black text-yellow-400 tracking-widest hover:text-yellow-300 transition-colors uppercase drop-shadow-[0_0_15px_rgba(250,204,21,0.3)]"
          >
            LazyTeacher
          </Link>

          {/* Sekcja przycisków i informacji o użytkowniku po prawej stronie */}
          <div className="flex-1 flex justify-end items-center gap-4">
            {token && (
              <>
                <span className="hidden sm:inline text-sm text-zinc-400 font-medium">
                  Zalogowany jako: <span className="text-zinc-200">{username}</span>
                </span>
                <button
                  onClick={logout}
                  className="bg-yellow-400 hover:bg-yellow-500 text-black px-5 py-2 rounded-lg text-sm font-black transition-all shadow-lg shadow-yellow-400/10 active:scale-95 uppercase tracking-wide"
                >
                  Wyloguj
                </button>
              </>
            )}
          </div>

        </div>
      </div>
    </header>
  );
}