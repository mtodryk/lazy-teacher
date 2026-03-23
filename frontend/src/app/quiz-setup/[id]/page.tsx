'use client';

import { useEffect, useState, use } from 'react';
import { useRouter } from 'next/navigation';
import { useAuth } from '@/context/AuthContext';

interface Question {
  id: number;
  text: string;
  options: string[];
  correct: number;
}

export default function QuizSetupPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = use(params); // TEST_ID
  const { token } = useAuth();
  const router = useRouter();

  const [isLoading, setIsLoading] = useState(true);
  const [questions, setQuestions] = useState<Question[]>([]);
  const [errorMsg, setErrorMsg] = useState('');
  
  // Stany dla generowania linku
  const [generatedLink, setGeneratedLink] = useState('');
  const [isLinking, setIsLinking] = useState(false);

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

        if (!res.ok) throw new Error('Nie udało się pobrać danych testu.');
        const data = await res.json();
        
        if (data.questions && Array.isArray(data.questions)) {
          const formatted = data.questions.map((q: any) => {
            const sourceAnswers = q.answers || q.choices || [];
            return {
              id: q.id,
              text: q.text || q.question_text || '',
              options: sourceAnswers.map((a: any) => typeof a === 'object' ? a.text : a),
              correct: sourceAnswers.findIndex((a: any) => a.is_correct === true) !== -1 
                ? sourceAnswers.findIndex((a: any) => a.is_correct === true)
                : (q.correct_option_index ?? 0)
            };
          });
          setQuestions(formatted);
        }
        setIsLoading(false);
      } catch (err: any) {
        setErrorMsg(err.message);
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
    updated[qIdx].options[oIdx] = newText;
    setQuestions(updated);
  };

  const setCorrectAnswer = (qIdx: number, oIdx: number) => {
    const updated = [...questions];
    updated[qIdx].correct = oIdx;
    setQuestions(updated);
  };

  // FUNKCJA GENEROWANIA LINKU
  const handleGenerateLink = async () => {
    setIsLinking(true);
    try {
      // 1. Opcjonalnie: Tu możesz wysłać PATCH do backendu, żeby zapisać zmiany przed generowaniem linku
      
      const res = await fetch(`http://localhost:8000/api/tests/${id}/generate-link/`, {
        method: 'POST',
        headers: {
          'Authorization': `Token ${token}`,
          'Content-Type': 'application/json',
        },
      });

      if (!res.ok) throw new Error('Nie udało się wygenerować linku.');
      
      // Tworzymy link do FRONTENDU, a nie do API
      const frontendUrl = `${window.location.origin}/start-quiz/${id}`;
      setGeneratedLink(frontendUrl);
    } catch (err: any) {
      alert(err.message);
    } finally {
      setIsLinking(false);
    }
  };

  const copyToClipboard = () => {
    navigator.clipboard.writeText(generatedLink);
    alert("Skopiowano do schowka!");
  };

  if (isLoading) {
    return (
      <div className="min-h-[80vh] flex flex-col items-center justify-center p-4">
        <style>{`@keyframes wave { 0%, 100% { transform: translateY(0px); } 50% { transform: translateY(-15px); } }`}</style>
        <div className="bg-zinc-900 border border-zinc-800 rounded-[2.5rem] p-16 shadow-2xl text-center max-w-2xl w-full">
          <div className="flex justify-center items-center text-3xl font-black text-yellow-400 mb-8 tracking-widest uppercase italic">
            {"Generuję pytania...".split('').map((char, i) => (
              <span key={i} className="inline-block" style={{ animation: 'wave 1.5s ease-in-out infinite', animationDelay: `${i * 0.1}s` }}>
                {char === ' ' ? '\u00A0' : char}
              </span>
            ))}
          </div>
          <p className="text-zinc-400 text-lg font-bold animate-pulse uppercase tracking-widest">LazyTeacher analizuje materiały</p>
        </div>
      </div>
    );
  }

  return (
    <div className="max-w-7xl mx-auto px-4 py-12 animate-in fade-in slide-in-from-bottom-4 duration-700">
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-10 items-start">
        
        {/* LEWA KOLUMNA: EDYTOR */}
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
                {q.options.map((opt, oIdx) => (
                  <div key={oIdx} className={`p-5 rounded-[1.5rem] border-2 transition-all flex items-start gap-5 pr-8 ${q.correct === oIdx ? 'border-green-500 bg-green-500/5' : 'border-zinc-800 bg-zinc-950/50 hover:border-zinc-700'}`}>
                    <button onClick={() => setCorrectAnswer(qIdx, oIdx)} className={`w-12 h-12 flex-shrink-0 rounded-2xl flex items-center justify-center transition-all ${q.correct === oIdx ? 'bg-green-500 text-black shadow-lg' : 'bg-zinc-800 text-zinc-600 hover:text-zinc-400'}`}>
                      {q.correct === oIdx ? <span className="text-2xl font-bold">✓</span> : <div className="w-3 h-3 rounded-full bg-zinc-700"></div>}
                    </button>
                    <textarea
                      value={opt}
                      onChange={(e) => updateOptionText(qIdx, oIdx, e.target.value)}
                      onInput={(e) => adjustHeight(e.target as HTMLTextAreaElement)}
                      className={`bg-transparent outline-none w-full py-3 font-bold text-lg transition-all resize-none overflow-hidden min-h-[40px] leading-relaxed ${q.correct === oIdx ? 'text-green-400' : 'text-zinc-400 focus:text-white'}`}
                      rows={1}
                    />
                  </div>
                ))}
              </div>
            </div>
          ))}
        </div>

        {/* PRAWA KOLUMNA: FINALIZACJA I LINK */}
        <div className="lg:sticky lg:top-28">
          <div className="bg-zinc-900 border-2 border-yellow-400/30 p-10 rounded-[3rem] shadow-2xl flex flex-col items-center text-center relative overflow-hidden">
            <div className="w-20 h-20 bg-yellow-400/10 rounded-[2rem] flex items-center justify-center mb-8 text-yellow-400 shadow-inner">
              <svg className="w-10 h-10" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2.5" d="M13.828 10.172a4 4 0 00-5.656 0l-4 4a4 4 0 105.656 5.656l1.102-1.101m-.758-4.828a4 4 0 005.656 0l4-4a4 4 0 00-5.656-5.656l-1.1 1.1"></path></svg>
            </div>
            
            <h3 className="text-3xl font-black text-white mb-4 uppercase italic">Publikacja</h3>
            <p className="text-zinc-500 mb-10 text-sm leading-relaxed font-medium">Sprawdź treść pytań. Po zatwierdzeniu wygenerujemy unikalny link do Twojego quizu.</p>
            
            {/* PRZYCISK LUB LINK */}
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
                  <a 
                    href={generatedLink} 
                    target="_blank" 
                    className="text-yellow-400 font-bold text-sm break-all hover:underline block text-left pr-8"
                  >
                    {generatedLink}
                  </a>
                  <button 
                    onClick={copyToClipboard}
                    className="absolute top-4 right-4 text-zinc-500 hover:text-yellow-400 transition-colors"
                    title="Kopiuj link"
                  >
                    <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M8 5H6a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2v-1M8 5a2 2 0 002 2h2a2 2 0 002-2M8 5a2 2 0 012-2h2a2 2 0 012 2m0 0h2a2 2 0 012 2v3m2 4H10m0 0l3-3m-3 3l3 3"></path></svg>
                  </button>
                </div>
                <p className="text-green-500 text-[10px] font-black uppercase tracking-widest animate-pulse">Link aktywny i gotowy!</p>
              </div>
            )}
          </div>
        </div>

      </div>
    </div>
  );
}