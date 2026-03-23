'use client';

import { useEffect, useState, use } from 'react';
import { useAuth } from '@/context/AuthContext';
import { useRouter } from 'next/navigation';
import Link from 'next/link';

interface Answer {
  text: string;
  is_correct: boolean;
}

interface Question {
  id: number;
  text: string;
  answers: Answer[];
}

export default function StartQuizPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = use(params);
  const { token } = useAuth();
  const router = useRouter();
  
  const [isLoading, setIsLoading] = useState(true);
  const [isStarted, setIsStarted] = useState(false);
  const [questions, setQuestions] = useState<Question[]>([]);
  const [quizTitle, setQuizTitle] = useState('');
  const [currentIdx, setCurrentIdx] = useState(0);
  const [score, setScore] = useState(0);
  const [isFinished, setIsFinished] = useState(false);
  const [showReview, setShowReview] = useState(false);
  const [selectedAnswer, setSelectedAnswer] = useState<number | null>(null);
  const [isLocked, setIsLocked] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!token) return;

    const fetchQuiz = async () => {
      try {
        const res = await fetch(`http://localhost:8000/api/tests/${id}/`, {
            headers: { 'Authorization': `Token ${token}` }
        });
        
        if (!res.ok) throw new Error(`Błąd: ${res.status}`);
        
        const data = await res.json();
        
        // Wyciąganie tytułu - sprawdzamy różne możliwe klucze z backendu
        const title = data.document_title || data.document_name || data.title || `Quiz #${id}`;
        setQuizTitle(title);
        
        if (data.questions && data.questions.length > 0) {
          setQuestions(data.questions.map((q: any) => ({
            id: q.id,
            text: q.text,
            answers: q.answers || []
          })));
          setError(null);
        } else {
          throw new Error("Ten quiz nie ma pytań.");
        }
        setIsLoading(false);
      } catch (err: any) {
        console.error(err);
        setError(err.message);
        setIsLoading(false);
      }
    };
    fetchQuiz();
  }, [id, token]);

  const handleAnswerClick = (ansIdx: number, isCorrect: boolean) => {
    if (isLocked) return;
    setSelectedAnswer(ansIdx);
    setIsLocked(true);

    if (isCorrect) setScore(s => s + 1);

    setTimeout(() => {
      if (currentIdx + 1 < questions.length) {
        setCurrentIdx(c => c + 1);
        setSelectedAnswer(null);
        setIsLocked(false);
      } else {
        setIsFinished(true);
      }
    }, 1000);
  };

  // Czas: liczba pytań / 2, zaokrąglone w dół
  const estimatedTime = Math.floor(questions.length / 2);

  if (isLoading) {
    return (
      <div className="min-h-screen flex flex-col items-center justify-center bg-black">
        <div className="text-2xl font-black text-yellow-400 uppercase tracking-[0.3em] animate-pulse italic">
          LazyTeacher wczytuje...
        </div>
      </div>
    );
  }

  // --- WIDOK 1: LOBBY (PRZED STARTEM) ---
  if (!isStarted && !isFinished && !showReview) {
    return (
      <div className="max-w-2xl mx-auto px-4 py-20 animate-in fade-in zoom-in-95 duration-700">
        <div className="bg-zinc-900 border-2 border-yellow-400/30 p-12 rounded-[3rem] shadow-2xl text-center relative overflow-hidden">
          <div className="absolute top-0 left-0 w-full h-2 bg-yellow-400 shadow-[0_0_15px_rgba(250,204,21,0.5)]"></div>
          
          <span className="text-yellow-400 font-black uppercase text-xs tracking-[0.4em] mb-4 block">Gotowy na wyzwanie?</span>
          <h1 className="text-5xl font-black text-white uppercase italic mb-10 tracking-tighter leading-tight">
            {quizTitle}
          </h1>
          
          <div className="bg-zinc-950/50 rounded-3xl p-8 border border-zinc-800 mb-12">
            <div className="grid grid-cols-2 gap-4 text-zinc-400">
              <div className="border-r border-zinc-800">
                <p className="text-[10px] uppercase font-black tracking-widest mb-1">Pytania</p>
                <p className="text-3xl font-black text-white">{questions.length}</p>
              </div>
              <div>
                <p className="text-[10px] uppercase font-black tracking-widest mb-1">Czas</p>
                <p className="text-3xl font-black text-white">{estimatedTime} min</p>
              </div>
            </div>
          </div>

          <button 
            onClick={() => setIsStarted(true)}
            className="w-full py-8 bg-yellow-400 hover:bg-yellow-300 text-black font-black rounded-[2rem] border-b-8 border-yellow-600 uppercase tracking-[0.2em] text-2xl active:scale-95 transition-all shadow-[0_20px_50px_rgba(250,204,21,0.2)]"
          >
            Zacznij Test
          </button>
        </div>
      </div>
    );
  }

  // --- WIDOK 2: ARKUSZ ODPOWIEDZI (REVIEW) ---
  if (showReview) {
    return (
      <div className="max-w-4xl mx-auto px-4 py-12 animate-in fade-in duration-500">
        <div className="flex justify-between items-center mb-12">
          <h2 className="text-4xl font-black text-white uppercase italic tracking-tighter">Przegląd</h2>
          <button 
            onClick={() => setShowReview(false)} 
            className="bg-yellow-400 text-black font-black px-8 py-3 rounded-2xl uppercase text-[11px] tracking-widest border-b-4 border-yellow-600 active:scale-95 transition-all"
          >
            Wróć do wyniku
          </button>
        </div>
        <div className="space-y-8">
          {questions.map((q, qIdx) => (
            <div key={q.id} className="bg-zinc-900 border border-zinc-800 p-8 rounded-[2.5rem] shadow-xl">
              <p className="text-white text-xl font-bold mb-8 leading-relaxed tracking-tight">{q.text}</p>
              <div className="grid grid-cols-1 gap-4">
                {q.answers.map((ans, aIdx) => (
                  <div key={aIdx} className={`p-5 rounded-2xl border-2 flex justify-between items-center ${ans.is_correct ? 'border-green-500 bg-green-500/5' : 'border-zinc-800 bg-zinc-950'}`}>
                    <span className={`font-bold ${ans.is_correct ? 'text-green-400' : 'text-zinc-500'}`}>{ans.text}</span>
                    {ans.is_correct && <div className="w-8 h-8 bg-green-500 text-black rounded-lg flex items-center justify-center font-black">✓</div>}
                  </div>
                ))}
              </div>
            </div>
          ))}
        </div>
      </div>
    );
  }

  // --- WIDOK 3: EKRAN KOŃCOWY ---
  if (isFinished) {
    return (
      <div className="max-w-2xl mx-auto px-4 py-20 animate-in zoom-in-95 duration-500">
        <div className="bg-zinc-900 border-2 border-yellow-400/30 p-12 rounded-[3rem] shadow-2xl text-center">
          <h1 className="text-6xl font-black text-white uppercase italic mb-4 tracking-tighter">Koniec!</h1>
          <p className="text-zinc-500 uppercase font-bold tracking-widest mb-10">Twój wynik:</p>
          
          <div className="text-8xl font-black text-yellow-400 mb-8 drop-shadow-[0_0_30px_rgba(250,204,21,0.3)]">
            {score}<span className="text-4xl text-zinc-700">/{questions.length}</span>
          </div>
          
          <button 
            onClick={() => setShowReview(true)}
            className="text-yellow-400 hover:text-yellow-300 font-black uppercase text-xs tracking-[0.3em] mb-14 transition-all block mx-auto underline decoration-2 underline-offset-8"
          >
            Zobacz poprawne odpowiedzi
          </button>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-6">
            <button 
              onClick={() => window.location.reload()}
              className="py-6 bg-yellow-400 hover:bg-yellow-300 text-black font-black rounded-2xl border-b-8 border-yellow-600 uppercase tracking-widest text-sm active:scale-95 transition-all"
            >
              Spróbuj ponownie
            </button>
            <Link 
              href="/" 
              className="py-6 bg-yellow-400 hover:bg-yellow-300 text-black font-black rounded-2xl border-b-8 border-yellow-600 uppercase tracking-widest text-sm active:scale-95 transition-all flex items-center justify-center"
            >
              Strona Główna
            </Link>
          </div>
        </div>
      </div>
    );
  }

  // --- WIDOK 4: AKTYWNE PYTANIE ---
  const currentQuestion = questions[currentIdx];
  return (
    <div className="max-w-4xl mx-auto px-4 py-12 animate-in fade-in duration-700">
      <div className="w-full h-1.5 bg-zinc-800 rounded-full mb-10 overflow-hidden">
        <div 
          className="h-full bg-yellow-400 transition-all duration-700 shadow-[0_0_15px_rgba(250,204,21,0.5)]" 
          style={{ width: `${((currentIdx + 1) / questions.length) * 100}%` }} 
        />
      </div>

      <div className="flex justify-between items-center mb-10 px-2">
        <span className="text-zinc-600 font-black text-xs uppercase tracking-widest">{currentIdx + 1} / {questions.length}</span>
        <span className="text-yellow-400/50 font-black text-xs uppercase tracking-[0.2em]">Fl33tApp Quiz</span>
      </div>

      <div className="bg-zinc-900 border border-zinc-800 p-10 sm:p-20 rounded-[3rem] shadow-2xl mb-8 relative">
        <h2 className="text-3xl sm:text-4xl font-black text-white text-center leading-tight mb-16 italic tracking-tighter">
          {currentQuestion?.text}
        </h2>
        <div className="grid grid-cols-1 gap-4">
          {currentQuestion?.answers.map((ans, idx) => {
            const isSelected = selectedAnswer === idx;
            const isCorrect = ans.is_correct;
            let btnStyle = "border-zinc-800 bg-zinc-950/40 text-zinc-300 hover:border-zinc-600";
            if (isSelected) btnStyle = isCorrect ? "border-green-500 bg-green-500/10 text-green-400 shadow-[0_0_30px_rgba(34,197,94,0.3)]" : "border-red-500 bg-red-500/10 text-red-400 shadow-[0_0_30px_rgba(239,68,68,0.3)]";
            
            return (
              <button 
                key={idx} 
                disabled={isLocked} 
                onClick={() => handleAnswerClick(idx, isCorrect)} 
                className={`p-6 rounded-[1.5rem] border-2 font-bold text-lg transition-all text-left flex items-center justify-between group ${btnStyle}`}
              >
                <span className="pr-4">{ans.text}</span>
                <div className={`w-10 h-10 flex-shrink-0 rounded-xl border-2 flex items-center justify-center transition-all ${isSelected ? 'border-current' : 'border-zinc-800'}`}>
                  {isSelected && (isCorrect ? '✓' : '✕')}
                </div>
              </button>
            );
          })}
        </div>
      </div>
    </div>
  );
}