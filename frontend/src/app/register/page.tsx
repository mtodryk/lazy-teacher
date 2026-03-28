'use client';

import { useState } from 'react';
import { useAuth } from '@/context/AuthContext';
import Link from 'next/link';
import { API_BASE_URL } from '@/lib/api';

export default function RegisterPage() {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [errorMsg, setErrorMsg] = useState('');
  // Używamy funkcji login z kontekstu, bo po poprawnej rejestracji od razu dostajemy token!
  const { login } = useAuth(); 

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setErrorMsg('');

    try {
      const res = await fetch(`${API_BASE_URL}/api/users/register/`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ username, password }),
      });

      // Próbujemy odczytać odpowiedź (może jej nie być przy błędzie CORS)
      const data = await res.json().catch(() => null);

      if (res.ok && data) {
        // Rejestracja udana! Backend od razu loguje i zwraca token
        login(data.username, data.token);
      } else {
        // Złapane błędy z Django (np. nazwa zajęta)
        console.error("Szczegóły błędu:", data);
        const errorMessage = data?.message || JSON.stringify(data?.extra) || 'Nieznany błąd zapytania.';
        setErrorMsg(`Nie udało się: ${errorMessage}`);
      }
    } catch (err) {
      console.error(err);
      // Ten błąd wyskoczy, gdy uderzymy w blokadę CORS
      setErrorMsg('Błąd połączenia. Przeglądarka zablokowała request (CORS) lub backend nie działa.');
    }
  };

  return (
    <div className="min-h-[80vh] flex items-center justify-center">
      <div className="bg-zinc-900 p-8 rounded-2xl border border-zinc-800 shadow-[0_0_30px_rgba(0,0,0,0.5)] w-full max-w-md">
        <h2 className="text-3xl font-black text-yellow-400 mb-6 text-center tracking-wide">Dołącz do LazyTeacher</h2>
        
        {/* Okienko wyświetlające błędy */}
        {errorMsg && (
          <div className="bg-red-950/50 border border-red-500/50 text-red-400 p-3 rounded-lg mb-6 text-sm text-center">
            {errorMsg}
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-sm font-bold text-zinc-400 mb-1">Nazwa użytkownika</label>
            <input
              type="text"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              className="w-full px-4 py-2 bg-zinc-800 border border-zinc-700 rounded-lg focus:ring-2 focus:ring-yellow-400 focus:border-transparent text-zinc-100 outline-none transition-all placeholder-zinc-600"
              placeholder="np. LazyTeacher123"
              required
            />
          </div>
          <div>
            <label className="block text-sm font-bold text-zinc-400 mb-1">Hasło (min. 8 znaków)</label>
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className="w-full px-4 py-2 bg-zinc-800 border border-zinc-700 rounded-lg focus:ring-2 focus:ring-yellow-400 focus:border-transparent text-zinc-100 outline-none transition-all placeholder-zinc-600"
              placeholder="••••••••"
              required
              minLength={8}
            />
          </div>
          <button
            type="submit"
            className="w-full bg-yellow-400 hover:bg-yellow-500 text-black font-black py-3 rounded-lg mt-6 shadow-[0_0_15px_rgba(250,204,21,0.2)] transition-all active:scale-95 uppercase tracking-widest"
          >
            Zarejestruj konto
          </button>
        </form>
        <p className="text-center text-zinc-500 mt-6 text-sm">
          Masz już konto?{' '}
          <Link href="/login" className="text-yellow-400 hover:text-yellow-300 font-bold underline underline-offset-4">
            Zaloguj się
          </Link>
        </p>
      </div>
    </div>
  );
}