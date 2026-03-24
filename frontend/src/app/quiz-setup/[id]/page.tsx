'use client';

import { useRouter, notFound } from 'next/navigation'; // ZMIANA: Dodano notFound/page.tsx]
import { useEffect, useState, use } from 'react';
import { useAuth } from '@/context/AuthContext';

interface Answer {
  id: number;
  text: string;
  is_correct: boolean;
}

interface Question {
  id: number;
  text: string;
  topic: string;
  answers: Answer[];
}

export default function QuizSetupPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = use(params); // TEST_ID
  const { token } = useAuth();
  const router = useRouter();

  const [isLoading, setIsLoading] = useState(true);
  const [questions, setQuestions] = useState<Question[]>([]);
  const [errorMsg, setErrorMsg] = useState('');
  
  // Stany dla zapisu i generowania linku
  const [isSaving, setIsSaving] = useState(false);
  const [saveSuccess, setSaveSuccess] = useState(false); 
  const [generatedLink, setGeneratedLink] = useState('');
  const [isLinking, setIsLinking] = useState(false);

  // --- NOWY STAN DLA OBSŁUGI BŁĘDU 500 (Błąd Krytyczny) ---/page.tsx]
  const [asyncError, setAsyncError] = useState<Error | null>(null);

  // Wyzwalacz dla globalnego pliku error.tsx
  if (asyncError) throw asyncError;

  const adjustHeight = (el: HTMLTextAreaElement | null) => {
    if (el) {
      el.style.height = 'auto';
      el.style.height = `${el.scrollHeight}px`;
    }
  };

  useEffect(() => {
    if (!token) return;

    const fetchTestData = async () => {
      try {
        const res = await fetch(`http://localhost:8000/api/tests/${id}/`, {
          method: 'GET',
          headers: {
            'Authorization': `Token ${token}`,
            'Content-Type': 'application/json',
          },
        });

        // Obsługa błędów przekierowująca na strony błędów/page.tsx]
        if (res.status === 404) notFound(); // Wyzwala not-found.tsx
        if (!res.ok) throw new Error(`Błąd API: ${res.status}`);

        const data = await res.json();
        
        if (data.questions && Array.isArray(data.questions)) {
          setQuestions(data.questions);
        }
        setIsLoading(false);
      } catch (err: any) {
        // Jeśli to błąd 404 od Next.js, pozwól mu działać/page.tsx]
        if (err.digest === 'NEXT_NOT_FOUND') throw err;
        console.error(err);
        setAsyncError(err); // Wszystkie inne błędy wyślą do strony 500 (error.tsx)
        setIsLoading(false);
      }
    };

    fetchTestData();
  }, [id, token]);

  useEffect(() => {
    if (!isLoading) {
      const timer = setTimeout(() => {
        const textareas = document.querySelectorAll('textarea');
        textareas.forEach((ta) => adjustHeight(ta as HTMLTextAreaElement));
      }, 100);
      return () => clearTimeout(timer);
    }
  }, [isLoading, questions]);

  const updateQuestionText = (qIdx: number, newText: string) => {
    const updated = [...questions];
    updated[qIdx].text = newText;
    setQuestions(updated);
  };

  const updateOptionText = (qIdx: number, oIdx: number, newText: string) => {
    const updated = [...questions];
    updated[qIdx].answers[oIdx].text = newText;
    setQuestions(updated);
  };

  const setCorrectAnswer = (qIdx: number, oIdx: number) => {
    const updated = [...questions];
    updated[qIdx].answers = updated[qIdx].answers.map((ans, idx) => ({
      ...ans,
      is_correct: idx === oIdx
    }));
    setQuestions(updated);
  };

  const handleSaveChanges = async () => {
    setIsSaving(true);
    try {
      const res = await fetch(`http://localhost:8000/api/tests/${id}/questions/`, {
        method: 'PATCH',
        headers: {
          'Authorization': `Token ${token}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ questions: questions })
      });

      if (res.status === 404) notFound();
      if (!res.ok) {
        const errorData = await res.json();
        throw new Error(errorData.message || 'Błąd podczas zapisywania zmian.');
      }

      setSaveSuccess(true);
      setTimeout(() => setSaveSuccess(false), 2000);

    } catch (err: any) {
      if (err.digest === 'NEXT_NOT_FOUND') throw err;
      console.error(err);
      setAsyncError(err);
    } finally {
      setIsSaving(false);
    }
  };

  const handleGenerateLink = async () => {
    setIsLinking(true);
    try {
      const res = await fetch(`http://localhost:8000/api/tests/${id}/generate-link/`, {
        method: 'POST',
        headers: {
          'Authorization': `Token ${token}`,
          'Content-Type': 'application/json',
        },
      });

      if (res.status === 404) notFound();
      if (!res.ok) throw new Error('Nie udało się wygenerować linku.');
      
      const data = await res.json();
      const frontendUrl = `${window.location.origin}/start-quiz/${data.code}`;
      setGeneratedLink(frontendUrl);
    } catch (err: any) {
      if (err.digest === 'NEXT_NOT_FOUND') throw err;
      console.error(err);
      setAsyncError(err);
    } finally {
      setIsLinking(false);
    }
  };

  const copyToClipboard = () => {
    navigator.clipboard.writeText(generatedLink);
  };

  if (isLoading) {
    return (
      <div className="min-h-[80vh] flex flex-col items-center justify-center p-4 bg-black">
        <div className="text-2xl font-black text-yellow-400 animate-pulse uppercase italic tracking-widest">Wczytywanie edytora...</div>
      </div>
    );
  }

  return (
    <div className="max-w-7xl mx-auto px-4 py-12 animate-in fade-in slide-in-from-bottom-4 duration-700">
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-10 items-start">
        
        <div className="lg:col-span-2 space-y-12">
          <h2 className="text-4xl font-black text-white uppercase italic tracking-tighter mb-4">Edycja Pytań</h2>
          
          {questions.map((q, qIdx) => (
            <div key={q.id || qIdx} className="bg-zinc-900 border border-zinc-800 p-10 rounded-[3rem] shadow-2xl hover:border-yellow-400/20 transition-all">
              <div className="flex items-start gap-6 mb-12">
                <div className="bg-yellow-400 text-black font-black w-14 h-14 flex-shrink-0 flex items-center justify-center rounded-[1.25rem] text-2xl shadow-lg">
                  {qIdx + 1}
                </div>
                <div className="flex-grow pt-1">
                  <label className="text-zinc-600 text-[11px] uppercase font-black tracking-[0.3em] mb-3 block">Treść pytania</label>
                  <textarea 
                    value={q.text} 
                    onChange={(e) => updateQuestionText(qIdx, e.target.value)}
                    onInput={(e) => adjustHeight(e.target as HTMLTextAreaElement)}
                    className="bg-transparent border-b-2 border-zinc-800 focus:border-yellow-400 outline-none text-white text-2xl font-black w-full py-2 transition-all resize-none overflow-hidden min-h-[60px]"
                    rows={1}
                  />
                </div>
              </div>
              
              <div className="grid grid-cols-1 gap-5">
                {q.answers.map((ans, oIdx) => (
                  <div key={ans.id || oIdx} className={`p-5 rounded-[1.5rem] border-2 transition-all flex items-start gap-5 pr-8 ${ans.is_correct ? 'border-green-500 bg-green-500/5' : 'border-zinc-800 bg-zinc-950/50 hover:border-zinc-700'}`}>
                    <button 
                      onClick={() => setCorrectAnswer(qIdx, oIdx)} 
                      className={`w-12 h-12 flex-shrink-0 rounded-2xl flex items-center justify-center transition-all ${ans.is_correct ? 'bg-green-500 text-black shadow-lg' : 'bg-zinc-800 text-zinc-600 hover:text-zinc-400'}`}
                    >
                      {ans.is_correct ? <span className="text-2xl font-bold">✓</span> : <div className="w-3 h-3 rounded-full bg-zinc-700"></div>}
                    </button>
                    <textarea
                      value={ans.text}
                      onChange={(e) => updateOptionText(qIdx, oIdx, e.target.value)}
                      onInput={(e) => adjustHeight(e.target as HTMLTextAreaElement)}
                      className={`bg-transparent outline-none w-full py-3 font-bold text-lg transition-all resize-none overflow-hidden min-h-[40px] leading-relaxed ${ans.is_correct ? 'text-green-400' : 'text-zinc-400 focus:text-white'}`}
                      rows={1}
                    />
                  </div>
                ))}
              </div>
            </div>
          ))}
        </div>

        <div className="lg:sticky lg:top-28">
          <div className="bg-zinc-900 border-2 border-yellow-400/30 p-10 rounded-[3rem] shadow-2xl flex flex-col items-center text-center relative overflow-hidden">
            <div className="w-20 h-20 bg-yellow-400/10 rounded-[2rem] flex items-center justify-center mb-8 text-yellow-400 shadow-inner">
              <svg className="w-10 h-10" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2.5" d="M8 7H5a2 2 0 00-2 2v9a2 2 0 002 2h14a2 2 0 002-2V9a2 2 0 00-2-2h-3m-1 4l-3 3m0 0l-3-3m3 3V4"></path></svg>
            </div>
            
            <h3 className="text-3xl font-black text-white mb-4 uppercase italic">Panel Akcji</h3>
            <p className="text-zinc-500 mb-10 text-sm leading-relaxed font-medium">Zatwierdź zmiany w treści pytań przed wygenerowaniem linku dla uczniów.</p>
            
            <div className="flex flex-col gap-4 w-full">
              <button 
                onClick={handleSaveChanges}
                disabled={isSaving || saveSuccess}
                className={`w-full py-6 text-black font-black rounded-[1.5rem] transition-all active:scale-95 uppercase tracking-widest border-b-8 disabled:opacity-50 shadow-lg ${saveSuccess ? 'bg-green-400 border-green-600' : 'bg-green-500 hover:bg-green-400 border-green-700'}`}
              >
                {isSaving ? 'Zapisywanie...' : (saveSuccess ? 'Zapisano!' : 'Zatwierdź zmiany')}
              </button>

              <div className="h-px bg-zinc-800 w-full my-4"></div>

              {!generatedLink ? (
                <button 
                  onClick={handleGenerateLink}
                  disabled={isLinking}
                  className="w-full py-6 bg-yellow-400 hover:bg-yellow-300 text-black font-black rounded-[1.5rem] transition-all active:scale-95 uppercase tracking-widest shadow-[0_20px_50px_rgba(250,204,21,0.15)] border-b-8 border-yellow-600 disabled:opacity-50"
                >
                  {isLinking ? 'Generowanie...' : 'Generuj Link'}
                </button>
              ) : (
                <div className="w-full animate-in zoom-in-95 duration-500">
                  <div className="bg-zinc-950 border border-yellow-400/50 p-4 rounded-2xl mb-4 group relative">
                    <p className="text-[10px] text-zinc-500 uppercase font-black tracking-widest mb-1 text-left">Twój link:</p>
                    <div className="flex items-center gap-2">
                       <a 
                         href={generatedLink} 
                         target="_blank" 
                         className="text-yellow-400 font-bold text-xs break-all hover:underline block text-left flex-1"
                       >
                         {generatedLink}
                       </a>
                       <button 
                         onClick={copyToClipboard}
                         className="text-zinc-500 hover:text-yellow-400 transition-colors"
                         title="Kopiuj"
                       >
                         <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M8 5H6a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2v-1M8 5a2 2 0 002 2h2a2 2 0 002-2M8 5a2 2 0 012-2h2a2 2 0 012 2m0 0h2a2 2 0 012 2v3m2 4H10m0 0l3-3m-3 3l3 3"></path></svg>
                       </button>
                    </div>
                  </div>
                  <p className="text-green-500 text-[10px] font-black uppercase tracking-widest animate-pulse italic">Test udostępniony!</p>
                </div>
              )}
            </div>
          </div>
        </div>

      </div>
    </div>
  );
}