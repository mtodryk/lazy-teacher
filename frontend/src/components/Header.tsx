'use client';

import { useState } from 'react';
import Link from 'next/link';
import { useAuth } from '@/context/AuthContext';

export default function Header() {
  const { token, username, logout } = useAuth();
  const [menuOpen, setMenuOpen] = useState(false);

  return (
    <header className="fixed top-0 left-0 w-full z-50 bg-zinc-900 border-b border-zinc-800 text-zinc-100 shadow-xl">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between items-center h-16 sm:h-20">
          {/* Po lewej: Moje Testy (desktop) */}
          <div className="hidden sm:flex flex-1">
            {token && (
              <Link
                href="/my-tests"
                className="bg-yellow-400 hover:bg-yellow-300 text-black px-5 py-2 rounded-lg text-sm font-black transition-all shadow-lg shadow-yellow-400/10 active:scale-95 uppercase tracking-wide"
              >
                Moje Testy
              </Link>
            )}
          </div>

          {/* Wyśrodkowana nazwa */}
          <Link
            href="/"
            className="text-2xl sm:text-4xl lg:text-5xl font-black text-yellow-400 tracking-widest hover:text-yellow-300 transition-colors uppercase drop-shadow-[0_0_15px_rgba(250,204,21,0.3)] sm:absolute sm:left-1/2 sm:-translate-x-1/2"
          >
            LazyTeacher
          </Link>

          {/* Po prawej: Desktop nav */}
          <div className="hidden sm:flex flex-1 justify-end items-center gap-4">
            {token && (
              <>
                <span className="hidden md:inline text-sm text-zinc-400 font-medium">
                  Zalogowany jako: <span className="text-zinc-200">{username}</span>
                </span>
                <button
                  onClick={logout}
                  className="bg-zinc-800 hover:bg-zinc-700 text-zinc-300 px-5 py-2 rounded-lg text-sm font-bold transition-all active:scale-95 uppercase tracking-wide border border-zinc-700"
                >
                  Wyloguj
                </button>
              </>
            )}
          </div>

          {/* Mobile hamburger */}
          {token && (
            <button
              onClick={() => setMenuOpen(!menuOpen)}
              className="sm:hidden p-2 text-zinc-400 hover:text-white transition-colors"
              aria-label="Menu"
            >
              <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                {menuOpen ? (
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                ) : (
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16M4 18h16" />
                )}
              </svg>
            </button>
          )}
        </div>

        {/* Mobile dropdown menu */}
        {menuOpen && token && (
          <div className="sm:hidden border-t border-zinc-800 py-4 space-y-3">
            <div className="text-sm text-zinc-400 font-medium px-2">
              Zalogowany jako: <span className="text-zinc-200">{username}</span>
            </div>
            <Link
              href="/my-tests"
              onClick={() => setMenuOpen(false)}
              className="block bg-yellow-400 hover:bg-yellow-300 text-black px-5 py-3 rounded-lg text-sm font-black transition-all active:scale-95 uppercase tracking-wide text-center"
            >
              Moje Testy
            </Link>
            <button
              onClick={() => { logout(); setMenuOpen(false); }}
              className="w-full bg-zinc-800 hover:bg-zinc-700 text-zinc-300 px-5 py-3 rounded-lg text-sm font-bold transition-all active:scale-95 uppercase tracking-wide border border-zinc-700"
            >
              Wyloguj
            </button>
          </div>
        )}
      </div>
    </header>
  );
}
