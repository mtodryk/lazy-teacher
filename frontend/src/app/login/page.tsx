'use client';

import { useState } from 'react';
import { useAuth } from '@/context/AuthContext';
import { useRouter } from 'next/navigation';
import Link from 'next/link';

export default function LoginPage() {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const { login } = useAuth();
  const router = useRouter();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      const response = await fetch('http://127.0.0.1:8000/api/users/login/', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ username, password }),
      });

      if (!response.ok) {
        throw new Error('Login failed');
      }

      const data = await response.json();
      login(username, data.token);
      router.push('/');
    } catch (err) {
      console.error('Login error:', err);
      alert('Nieprawidłowe dane logowania');
    }
  };

  return (
    <div className="min-h-[80vh] flex items-center justify-center">
      <div className="bg-zinc-900 p-8 rounded-2xl border border-zinc-800 shadow-[0_0_30px_rgba(0,0,0,0.5)] w-full max-w-md">
        <h2 className="text-3xl font-bold text-yellow-400 mb-2 text-center">Witaj ponownie</h2>
        <p className="text-zinc-500 text-center mb-8 text-sm">Zaloguj się do swojego konta</p>

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-zinc-400 mb-1">Nazwa użytkownika</label>
            <input
              type="text"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              className="w-full px-4 py-2 bg-zinc-800 border border-zinc-700 rounded-lg focus:ring-2 focus:ring-yellow-500 focus:border-transparent text-white outline-none transition-all placeholder-zinc-600"
              placeholder="Twój login"
              required
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-zinc-400 mb-1">Hasło</label>
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className="w-full px-4 py-2 bg-zinc-800 border border-zinc-700 rounded-lg focus:ring-2 focus:ring-yellow-500 focus:border-transparent text-white outline-none transition-all placeholder-zinc-600"
              placeholder="••••••••"
              required
            />
          </div>
          <button
            type="submit"
            className="w-full bg-yellow-400 hover:bg-yellow-500 text-black font-black py-3 rounded-lg mt-6 shadow-lg shadow-yellow-400/10 transition-all active:scale-[0.98] uppercase tracking-wider"
          >
            Zaloguj się
          </button>
        </form>
        <p className="text-center text-zinc-500 mt-6 text-sm">
          Nie masz konta?{' '}
          <Link href="/register" className="text-yellow-400 hover:text-yellow-300 font-bold underline">
            Stwórz je tutaj
          </Link>
        </p>
      </div>
    </div>
  );
}
