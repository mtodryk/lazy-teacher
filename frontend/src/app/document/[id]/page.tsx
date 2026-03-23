'use client';

import { useEffect, useState, use } from 'react';
import { useAuth } from '@/context/AuthContext';
import { useRouter } from 'next/navigation';
import Link from 'next/link';

type DocStatus = 'pending' | 'processing' | 'ready' | 'error';

export default function DocumentLoadingPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = use(params); // To jest ID DOKUMENTU
  const { token } = useAuth();
  const router = useRouter();

  const [status, setStatus] = useState<DocStatus>('pending');
  const [docTitle, setDocTitle] = useState('');
  const [errorMsg, setErrorMsg] = useState('');
  const [minTimeElapsed, setMinTimeElapsed] = useState(false);
  const [topicsRequested, setTopicsRequested] = useState(false);
  const [isGenerating, setIsGenerating] = useState(false); // Nowy stan dla przycisku

  useEffect(() => {
    if (!token) return;

    // Licznik dla efektu wizualnego ładowania
    const timer = setTimeout(() => setMinTimeElapsed(true), 3000);

    const checkStatus = async () => {
      try {
        const res = await fetch(`http://localhost:8000/api/documents/${id}/`, {
          method: 'GET',
          headers: {
            'Authorization': `Token ${token}`,
            'Content-Type': 'application/json',
          },
        });

        if (!res.ok) throw new Error('Nie udało się pobrać statusu dokumentu.');

        const data = await res.json();
        setDocTitle(data.title);
        const currentStatus = data.status.toLowerCase() as DocStatus;
        setStatus(currentStatus);

        // --- KLUCZOWA LOGIKA: AUTOMATYCZNE EXTRACT-TOPICS ---
        if (currentStatus === 'ready' && !topicsRequested) {
          handleExtractTopics();
        }

        if (currentStatus === 'ready' || currentStatus === 'error') {
          clearInterval(pollingInterval);
        }
      } catch (err) {
        console.error(err);
        setErrorMsg('Błąd połączenia z serwerem.');
        clearInterval(pollingInterval);
      }
    };

    const handleExtractTopics = async () => {
      setTopicsRequested(true);
      try {
        await fetch(`http://localhost:8000/api/documents/${id}/extract-topics/`, {
          method: 'POST',
          headers: {
            'Authorization': `Token ${token}`,
            'Content-Type': 'application/json',
          },
        });
        console.log("Sukces: Tematy są wyciągane!");
      } catch (err) {
        console.error("Błąd sieciowy przy extract-topics:", err);
      }
    };

    checkStatus();
    const pollingInterval = setInterval(checkStatus, 2000);

    return () => {
      clearInterval(pollingInterval);
      clearTimeout(timer);
    };
  }, [id, token, topicsRequested]);

  // --- NOWA LOGIKA: GENEROWANIE QUIZU PO KLIKNIĘCIU ---
  const handleGenerateQuiz = async () => {
    setIsGenerating(true);
    try {
      const res = await fetch(`http://localhost:8000/api/documents/${id}/generate-quiz/`, {
        method: 'POST',
        headers: {
          'Authorization': `Token ${token}`,
          'Content-Type': 'application/json',
        },
      });

      if (!res.ok) throw new Error('Nie udało się wygenerować quizu.');

      const data = await res.json();
      
      // Pobieramy test_id z odpowiedzi backendu
      const testId = data.id || data.test_id;

      if (testId) {
        router.push(`/quiz-setup/${testId}`);
      } else {
        alert("Backend nie zwrócił ID testu.");
        setIsGenerating(false);
      }
    } catch (err: any) {
      console.error(err);
      alert("Wystąpił błąd podczas generowania: " + err.message);
      setIsGenerating(false);
    }
  };

  const isActuallyReady = status === 'ready' && minTimeElapsed;

  const WavingText = ({ text }: { text: string }) => (
    <div className="flex justify-center items-center text-3xl font-black text-yellow-400 mb-8 tracking-widest drop-shadow-[0_0_10px_rgba(250,204,21,0.5)]">
      {text.split('').map((char, i) => (
        <span key={i} className="inline-block" style={{ animation: 'wave 1.5s ease-in-out infinite', animationDelay: `${i * 0.1}s` }}>
          {char === ' ' ? '\u00A0' : char}
        </span>
      ))}
    </div>
  );

  return (
    <div className="max-w-5xl mx-auto px-4 py-12">
      <style>{`@keyframes wave { 0%, 100% { transform: translateY(0px); } 50% { transform: translateY(-15px); } }`}</style>

      {/* --- EKRAN ŁADOWANIA --- */}
      {!isActuallyReady && status !== 'error' && (
        <div className="min-h-[60vh] flex flex-col items-center justify-center bg-zinc-900/50 border border-zinc-800 rounded-3xl p-16 shadow-2xl backdrop-blur-sm">
          <WavingText text="LazyTeacher analizuje..." />
          <p className="text-zinc-400 text-lg font-medium animate-pulse tracking-wide uppercase">Przygotowujemy grunt pod Twój sukces</p>
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

          <h1 className="text-6xl font-black text-white tracking-tighter uppercase italic">Gotowe do nauki</h1>
          <p className="text-zinc-500 text-xl font-medium tracking-tight">Dokument: <span className="text-yellow-400 border-b-2 border-yellow-400/30">{docTitle}</span></p>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-8 mt-4 w-full">
            
            {/* Lewe: Przeglądanie Tematów */}
            <div className="bg-zinc-900 border border-zinc-800 p-10 rounded-[2.5rem] flex flex-col items-center text-center shadow-2xl hover:border-yellow-400/40 transition-all group">
              <div className="w-20 h-20 bg-yellow-400/10 rounded-3xl flex items-center justify-center mb-6 text-yellow-400 group-hover:scale-110 transition-transform shadow-inner">
                <svg className="w-10 h-10" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2.5" d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2"></path></svg>
              </div>
              <h3 className="text-2xl font-black text-white mb-4 uppercase tracking-tight">Tematyka</h3>
              <p className="text-zinc-500 mb-8 text-sm leading-relaxed max-w-[200px]">System wyodrębnił kluczowe tematy z Twoich notatek.</p>
              <button className="w-full py-5 bg-yellow-400 hover:bg-yellow-300 text-black font-black rounded-2xl transition-all active:scale-95 uppercase tracking-tighter shadow-xl border-b-4 border-yellow-600">
                Przeglądaj Zagadnienia
              </button>
            </div>

            {/* Prawe: Generator Quizu */}
            <div className="bg-zinc-900 border border-zinc-800 p-10 rounded-[2.5rem] flex flex-col items-center text-center shadow-2xl hover:border-yellow-400/40 transition-all group">
              <div className="w-20 h-20 bg-yellow-400/10 rounded-3xl flex items-center justify-center mb-6 text-yellow-400 group-hover:scale-110 transition-transform shadow-inner">
                <svg className="w-10 h-10" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2.5" d="M13 10V3L4 14h7v7l9-11h-7z"></path></svg>
              </div>
              <h3 className="text-2xl font-black text-white mb-4 uppercase tracking-tight">Start Testu</h3>
              <p className="text-zinc-500 mb-8 text-sm leading-relaxed max-w-[200px]">Przejdź do generowania pytań i przygotowania quizu.</p>
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
        <div className="min-h-[60vh] flex flex-col items-center justify-center bg-zinc-900 border border-zinc-800 rounded-[2.5rem] p-16 shadow-2xl text-center">
          <div className="w-24 h-24 bg-red-500/10 rounded-full flex items-center justify-center mb-8">
            <svg className="w-12 h-12 text-red-500" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="3" d="M6 18L18 6M6 6l12 12"></path></svg>
          </div>
          <h2 className="text-4xl font-black text-red-500 mb-4 uppercase italic">Błąd</h2>
          <p className="text-zinc-400 mb-12 text-xl max-w-md">{errorMsg || "Coś poszło nie tak podczas analizy."}</p>
          <Link href="/upload" className="bg-zinc-800 hover:bg-zinc-700 text-white font-black px-12 py-4 rounded-2xl transition-all active:scale-95 uppercase tracking-widest border border-zinc-700">Wróć</Link>
        </div>
      )}
    </div>
  );
}