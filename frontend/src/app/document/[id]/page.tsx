'use client';

import { useRouter, notFound } from 'next/navigation';
import { useEffect, useState, useCallback, use } from 'react';
import { useAuth } from '@/context/AuthContext';
import Link from 'next/link';

type DocStatus = 'pending' | 'processing' | 'ready' | 'error' | 'topics_extracted';

export default function DocumentLoadingPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = use(params);
  const { token, logout } = useAuth();
  const router = useRouter();

  // Istniejące stany
  const [status, setStatus] = useState<DocStatus>('pending');
  const [docTitle, setDocTitle] = useState('');
  const [errorMsg, setErrorMsg] = useState('');
  const [minTimeElapsed, setMinTimeElapsed] = useState(false);
  const [topicsRequested, setTopicsRequested] = useState(false);
  const [isGenerating, setIsGenerating] = useState(false);

  // Stany dla zagadnień i pobierania
  const [topics, setTopics] = useState<string[]>([]);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [newTopic, setNewTopic] = useState('');
  const [isManaging, setIsManaging] = useState(false);
  const [isDownloading, setIsDownloading] = useState(false);

  // Toast notifications
  const [toasts, setToasts] = useState<{ id: number; message: string; type: 'error' | 'info' }[]>([]);

  const showToast = useCallback((message: string, type: 'error' | 'info' = 'error') => {
    const toastId = Date.now();
    setToasts((prev) => [...prev, { id: toastId, message, type }]);
    setTimeout(() => setToasts((prev) => prev.filter((t) => t.id !== toastId)), 4000);
  }, []);

  // --- NOWY STAN DLA OBSŁUGI BŁĘDU 500 ---
  const [asyncError, setAsyncError] = useState<Error | null>(null);

  // Wyzwalacz dla globalnego pliku error.tsx
  if (asyncError) throw asyncError;

  useEffect(() => {
    if (!localStorage.getItem('token')) {
      router.push('/login');
      return;
    }
    if (!token) return;

    const timer = setTimeout(() => setMinTimeElapsed(true), 3000);

    const checkStatus = async () => {
      try {
        const res = await fetch(`http://localhost:8000/api/documents/${id}/`, {
          method: 'GET',
          headers: {
            Authorization: `Token ${token}`,
            'Content-Type': 'application/json'
          }
        });

        if (res.status === 401) {
          logout();
          return;
        }
        if (res.status === 404) notFound();
        if (!res.ok) throw new Error(`Błąd serwera: ${res.status}`);

        const data = await res.json();
        setDocTitle(data.title);
        const currentStatus = data.status.toLowerCase() as DocStatus;
        setStatus(currentStatus);

        if (currentStatus === 'topics_extracted' && !topicsRequested) {
          handleExtractTopics();
        }

        if (currentStatus === 'topics_extracted' || currentStatus === 'error') {
          clearInterval(pollingInterval);
        }
      } catch (err: any) {
        // Jeśli to nie jest błąd 404 od Next.js, ustaw błąd asynchroniczny dla error.tsx
        if (err.digest === 'NEXT_NOT_FOUND') throw err;
        console.error(err);
        setAsyncError(err);
        clearInterval(pollingInterval);
      }
    };

    const handleExtractTopics = async () => {
      setTopicsRequested(true);
      try {
        const response = await fetch(`http://localhost:8000/api/documents/${id}/topics/`, {
          method: 'GET',
          headers: {
            Authorization: `Token ${token}`,
            'Content-Type': 'application/json'
          }
        });

        if (response.ok) {
          const data = await response.json();
          setTopics(data.topics || []);
        }
      } catch (err) {
        console.error('Błąd sieciowy przy pobieraniu tematów:', err);
      }
    };

    checkStatus();
    const pollingInterval = setInterval(checkStatus, 2000);

    return () => {
      clearInterval(pollingInterval);
      clearTimeout(timer);
    };
  }, [id, token, topicsRequested]);

  // --- LOGIKA POBIERANIA / OTWIERANIA DOKUMENTU ---
  const handleDownloadDocument = async () => {
    setIsDownloading(true);
    try {
      const res = await fetch(`http://localhost:8000/api/documents/${id}/download-url/`, {
        method: 'GET',
        headers: {
          Authorization: `Token ${token}`,
          'Content-Type': 'application/json'
        }
      });

      if (res.status === 404) notFound();
      if (!res.ok) throw new Error('Nie udało się wygenerować linku do pliku.');

      const data = await res.json();

      if (data.url) {
        window.open(data.url, '_blank');
      } else {
        showToast('Backend nie zwrócił adresu URL.');
      }
    } catch (err: any) {
      if (err.digest === 'NEXT_NOT_FOUND') throw err;
      console.error(err);
      setAsyncError(err);
    } finally {
      setIsDownloading(false);
    }
  };

  const handleAddTopic = async () => {
    if (!newTopic.trim()) return;
    setIsManaging(true);
    try {
      const res = await fetch(`http://localhost:8000/api/documents/${id}/topics/manage/`, {
        method: 'POST',
        headers: {
          Authorization: `Token ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ topic: newTopic.trim() })
      });

      if (res.status === 404) notFound();
      if (!res.ok) throw new Error('Nie udało się dodać tematu');
      const data = await res.json();
      setTopics(data.topics);
      setNewTopic('');
    } catch (err: any) {
      if (err.digest === 'NEXT_NOT_FOUND') throw err;
      console.error(err);
      setAsyncError(err);
    } finally {
      setIsManaging(false);
    }
  };

  const handleDeleteTopic = async (topicToDelete: string) => {
    setIsManaging(true);
    try {
      const res = await fetch(`http://localhost:8000/api/documents/${id}/topics/manage/`, {
        method: 'DELETE',
        headers: {
          Authorization: `Token ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ topic: topicToDelete })
      });

      if (res.status === 404) notFound();
      if (!res.ok) throw new Error('Nie udało się usunąć tematu');
      const data = await res.json();
      setTopics(data.topics);
    } catch (err: any) {
      if (err.digest === 'NEXT_NOT_FOUND') throw err;
      console.error(err);
      setAsyncError(err);
    } finally {
      setIsManaging(false);
    }
  };

  const handleGenerateQuiz = async () => {
    setIsGenerating(true);
    try {
      const res = await fetch(`http://localhost:8000/api/documents/${id}/generate-quiz/`, {
        method: 'POST',
        headers: {
          Authorization: `Token ${token}`,
          'Content-Type': 'application/json'
        }
      });

      if (res.status === 404) notFound();
      if (!res.ok) throw new Error('Nie udało się wygenerować quizu.');

      const data = await res.json();
      const testId = data.id || data.test_id;

      if (testId) {
        router.push(`/quiz-setup/${testId}`);
      } else {
        showToast('Backend nie zwrócił ID testu.');
        setIsGenerating(false);
      }
    } catch (err: any) {
      if (err.digest === 'NEXT_NOT_FOUND') throw err;
      console.error(err);
      setAsyncError(err);
      setIsGenerating(false);
    }
  };

  const isActuallyReady = status === 'topics_extracted' && minTimeElapsed;

  const WavingText = ({ text }: { text: string }) => (
    <div className="flex justify-center items-center text-xl sm:text-2xl md:text-3xl font-black text-yellow-400 mb-6 sm:mb-8 tracking-widest drop-shadow-[0_0_10px_rgba(250,204,21,0.5)]">
      {text.split('').map((char, i) => (
        <span
          key={i}
          className="inline-block"
          style={{
            animation: 'wave 1.5s ease-in-out infinite',
            animationDelay: `${i * 0.1}s`
          }}
        >
          {char === ' ' ? '\u00A0' : char}
        </span>
      ))}
    </div>
  );

  return (
    <div className="max-w-5xl mx-auto px-4 py-12">
      {/* Toast notifications */}
      <div className="fixed top-24 right-4 z-[100] flex flex-col gap-3 pointer-events-none">
        {toasts.map((toast) => (
          <div
            key={toast.id}
            className={`pointer-events-auto animate-in slide-in-from-right-5 duration-300 max-w-sm p-4 rounded-2xl border shadow-2xl backdrop-blur-sm ${
              toast.type === 'error'
                ? 'bg-red-500/10 border-red-500/30 text-red-400'
                : 'bg-yellow-400/10 border-yellow-400/30 text-yellow-400'
            }`}
          >
            <p className="text-sm font-bold leading-snug">{toast.message}</p>
          </div>
        ))}
      </div>

      <style>{`@keyframes wave { 0%, 100% { transform: translateY(0px); } 50% { transform: translateY(-15px); } }`}</style>

      {/* --- EKRAN ŁADOWANIA --- */}
      {!isActuallyReady && status !== 'error' && (
        <div className="min-h-[60vh] flex flex-col items-center justify-center bg-zinc-900/50 border border-zinc-800 rounded-2xl sm:rounded-3xl p-6 sm:p-16 shadow-2xl backdrop-blur-sm">
          <WavingText text="LAZY TEACHER analizuje..." />
          <p className="text-sm sm:text-base md:text-lg font-medium animate-pulse tracking-wide uppercase text-zinc-400">
            Przygotowujemy grunt pod Twój sukces
          </p>
          <div className="w-64 h-1.5 bg-zinc-800 rounded-full mt-10 overflow-hidden relative shadow-[0_0_15px_rgba(0,0,0,0.5)]">
            <div className="absolute top-0 left-0 h-full bg-yellow-400 w-1/2 animate-[progress_2s_linear_infinite]"></div>
          </div>
          <style>{` @keyframes progress { 0% { left: -100%; } 100% { left: 100%; } } `}</style>
        </div>
      )}

      {/* --- PANEL SUKCESU --- */}
      {isActuallyReady && (
        <div className="animate-in fade-in slide-in-from-bottom-6 duration-700 flex flex-col gap-10 text-center items-center">
          <div className="inline-flex items-center gap-2 px-4 py-1.5 rounded-full bg-green-500/10 border border-green-500/20 text-green-400 text-sm font-bold uppercase tracking-wider mb-2">
            <span className="w-2 h-2 bg-green-500 rounded-full animate-ping"></span>
            Analiza Gotowa
          </div>

          <h1 className="text-3xl sm:text-5xl md:text-6xl font-black text-white tracking-tighter uppercase italic">
            Gotowe do nauki
          </h1>

          <p className="text-zinc-500 text-base sm:text-xl font-medium tracking-tight flex flex-wrap items-center justify-center gap-2">
            Dokument:
            <button
              onClick={handleDownloadDocument}
              disabled={isDownloading}
              title="Kliknij, aby pobrać lub otworzyć plik"
              className="text-yellow-400 border-b-2 border-yellow-400/30 hover:text-yellow-300 hover:border-yellow-300 transition-colors cursor-pointer focus:outline-none disabled:opacity-50 flex items-center gap-2"
            >
              {docTitle}
              {isDownloading ? (
                <svg className="w-5 h-5 animate-spin" fill="none" viewBox="0 0 24 24">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                  <path
                    className="opacity-75"
                    fill="currentColor"
                    d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
                  ></path>
                </svg>
              ) : (
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth="2"
                    d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14"
                  ></path>
                </svg>
              )}
            </button>
          </p>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-8 mt-4 w-full">
            <div className="bg-zinc-900 border border-zinc-800 p-6 sm:p-10 rounded-2xl sm:rounded-[2.5rem] flex flex-col items-center text-center shadow-2xl hover:border-yellow-400/40 transition-all group">
              <div className="w-16 h-16 sm:w-20 sm:h-20 bg-yellow-400/10 rounded-2xl sm:rounded-3xl flex items-center justify-center mb-4 sm:mb-6 text-yellow-400 group-hover:scale-110 transition-transform shadow-inner">
                <svg className="w-8 h-8 sm:w-10 sm:h-10" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth="2.5"
                    d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2"
                  ></path>
                </svg>
              </div>
              <h3 className="text-xl sm:text-2xl font-black text-white mb-4 uppercase tracking-tight">Tematyka</h3>
              <p className="text-zinc-500 mb-8 text-sm leading-relaxed max-w-[200px]">
                System wyodrębnił kluczowe tematy z Twoich notatek.
              </p>
              <button
                onClick={() => setIsModalOpen(true)}
                className="w-full py-5 bg-yellow-400 hover:bg-yellow-300 text-black font-black rounded-2xl transition-all active:scale-95 uppercase tracking-tighter shadow-xl border-b-4 border-yellow-600"
              >
                Przeglądaj Zagadnienia
              </button>
            </div>

            <div className="bg-zinc-900 border border-zinc-800 p-6 sm:p-10 rounded-2xl sm:rounded-[2.5rem] flex flex-col items-center text-center shadow-2xl hover:border-yellow-400/40 transition-all group">
              <div className="w-16 h-16 sm:w-20 sm:h-20 bg-yellow-400/10 rounded-2xl sm:rounded-3xl flex items-center justify-center mb-4 sm:mb-6 text-yellow-400 group-hover:scale-110 transition-transform shadow-inner">
                <svg className="w-8 h-8 sm:w-10 sm:h-10" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth="2.5"
                    d="M13 10V3L4 14h7v7l9-11h-7z"
                  ></path>
                </svg>
              </div>
              <h3 className="text-xl sm:text-2xl font-black text-white mb-4 uppercase tracking-tight">Start Testu</h3>
              <p className="text-zinc-500 mb-8 text-sm leading-relaxed max-w-[200px]">
                Przejdź do generowania pytań i przygotowania quizu.
              </p>
              <button
                onClick={handleGenerateQuiz}
                disabled={isGenerating}
                className="w-full py-5 bg-yellow-400 hover:bg-yellow-300 text-black font-black rounded-2xl transition-all active:scale-95 uppercase tracking-tighter shadow-xl border-b-4 border-yellow-600 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {isGenerating ? 'Generuję...' : 'Generuj Quiz'}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* --- EKRAN BŁĘDU --- */}
      {(status === 'error' || errorMsg) && (
        <div className="min-h-[60vh] flex flex-col items-center justify-center bg-zinc-900 border border-zinc-800 rounded-2xl sm:rounded-[2.5rem] p-6 sm:p-16 shadow-2xl text-center">
          <div className="w-24 h-24 bg-red-500/10 rounded-full flex items-center justify-center mb-8">
            <svg className="w-12 h-12 text-red-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="3" d="M6 18L18 6M6 6l12 12"></path>
            </svg>
          </div>
          <h2 className="text-4xl font-black text-red-500 mb-4 uppercase italic">Błąd</h2>
          <p className="text-zinc-400 mb-12 text-xl max-w-md">{errorMsg || 'Coś poszło nie tak podczas analizy.'}</p>
          <Link
            href="/upload"
            className="bg-zinc-800 hover:bg-zinc-700 text-white font-black px-12 py-4 rounded-2xl transition-all active:scale-95 uppercase tracking-widest border border-zinc-700"
          >
            Wróć
          </Link>
        </div>
      )}

      {/* --- MODAL DO ZARZĄDZANIA TEMATAMI --- */}
      {isModalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/80 backdrop-blur-sm p-4 animate-in fade-in duration-200">
          <div className="bg-zinc-900 border border-zinc-800 rounded-2xl sm:rounded-[2.5rem] w-full max-w-2xl p-5 sm:p-8 shadow-2xl flex flex-col max-h-[85vh]">
            <div className="flex justify-between items-center mb-6">
              <h2 className="text-3xl font-black text-white uppercase italic">Zagadnienia</h2>
              <button
                onClick={() => setIsModalOpen(false)}
                className="text-zinc-500 hover:text-white transition-colors bg-zinc-800/50 hover:bg-zinc-800 p-2 rounded-full"
              >
                <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2.5" d="M6 18L18 6M6 6l12 12"></path>
                </svg>
              </button>
            </div>

            <div className="flex gap-3 mb-6">
              <input
                type="text"
                value={newTopic}
                onChange={(e) => setNewTopic(e.target.value)}
                placeholder="Dodaj nowe zagadnienie..."
                className="flex-1 bg-zinc-800 border border-zinc-700 rounded-2xl px-5 py-4 text-white focus:outline-none focus:border-yellow-400/50 transition-colors"
                onKeyDown={(e) => e.key === 'Enter' && handleAddTopic()}
                disabled={isManaging}
              />
              <button
                onClick={handleAddTopic}
                disabled={isManaging || !newTopic.trim()}
                className="bg-yellow-400 text-black font-black px-8 rounded-2xl hover:bg-yellow-300 disabled:opacity-50 disabled:cursor-not-allowed transition-all active:scale-95 uppercase tracking-tight"
              >
                Dodaj
              </button>
            </div>

            <div className="overflow-y-auto flex-1 pr-2 space-y-3 custom-scrollbar">
              {topics.length === 0 ? (
                <p className="text-zinc-500 text-center py-8 font-medium">Brak zagadnień. Dodaj pierwsze!</p>
              ) : (
                topics.map((topic, idx) => (
                  <div
                    key={idx}
                    className="flex justify-between items-center bg-zinc-800/30 border border-zinc-700/50 rounded-2xl p-4 group hover:border-yellow-400/30 transition-colors"
                  >
                    <span className="text-zinc-200 font-medium pl-2">{topic}</span>
                    <button
                      onClick={() => handleDeleteTopic(topic)}
                      disabled={isManaging}
                      className="text-red-500/50 hover:text-red-500 p-2.5 rounded-xl hover:bg-red-500/10 transition-colors disabled:opacity-50 active:scale-95"
                      title="Usuń"
                    >
                      <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path
                          strokeLinecap="round"
                          strokeLinejoin="round"
                          strokeWidth="2.5"
                          d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"
                        ></path>
                      </svg>
                    </button>
                  </div>
                ))
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
