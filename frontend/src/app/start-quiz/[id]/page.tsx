'use client';

import { useEffect, useState, useCallback, use } from 'react';
import { useRouter, notFound } from 'next/navigation';
import Link from 'next/link';

interface AnswerForShare {
  id: number;
  text: string;
}

interface QuestionForShare {
  id: number;
  text: string;
  topic: string;
  answers: AnswerForShare[];
}

interface QuizData {
  quiz_id: number;
  questions: QuestionForShare[];
}

interface AnswerSelection {
  questionId: number;
  answerId: number | null;
}

interface SubmissionResult {
  score: number;
  max_score: number;
  percentage: number;
  passed: boolean;
  answers: {
    question_id: number;
    correct_answer_id: number;
    selected_answer_id: number;
    is_correct: boolean;
  }[];
}

// Pomocnicza funkcja do tasowania tablicy (Algorytm Fisher-Yates)/page.tsx]
function shuffleArray<T>(array: T[]): T[] {
  const shuffled = [...array];
  for (let i = shuffled.length - 1; i > 0; i--) {
    const j = Math.floor(Math.random() * (i + 1));
    [shuffled[i], shuffled[j]] = [shuffled[j], shuffled[i]];
  }
  return shuffled;
}

export default function StartQuizPage({ params }: { params: Promise<{ id: string }> }) {
  const { id: quizCode } = use(params);
  const router = useRouter();

  const [isLoading, setIsLoading] = useState(true);
  const [isStarted, setIsStarted] = useState(false);

  const [quizId, setQuizId] = useState<number | null>(null);
  const [questions, setQuestions] = useState<QuestionForShare[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [studentName, setStudentName] = useState('');

  const [currentIdx, setCurrentIdx] = useState(0);
  const [selectedAnswers, setSelectedAnswers] = useState<AnswerSelection[]>([]);
  const [isReviewingBeforeSubmit, setIsReviewingBeforeSubmit] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);

  const [submissionResult, setSubmissionResult] = useState<SubmissionResult | null>(null);
  const [showResultReview, setShowResultReview] = useState(false);

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
    const fetchQuiz = async () => {
      try {
        const res = await fetch(`http://localhost:8000/api/quizes/by-code/${quizCode}/`, {
          method: 'GET',
          headers: { 'Content-Type': 'application/json' }
        });

        // Obsługa błędów przekierowująca na strony błędów
        if (res.status === 404) notFound(); // Wyzwala not-found.tsx
        if (!res.ok) throw new Error(`Błąd ładowania quizu: ${res.status}`);

        const data: QuizData = await res.json();

        if (data.questions && data.questions.length > 0) {
          const shuffledQuestions = shuffleArray(data.questions);
          const fullyShuffled = shuffledQuestions.map((q) => ({
            ...q,
            answers: shuffleArray(q.answers)
          }));

          setQuizId(data.quiz_id);
          setQuestions(fullyShuffled);
          setSelectedAnswers(fullyShuffled.map((q) => ({ questionId: q.id, answerId: null })));
        } else {
          throw new Error('Ten quiz nie ma pytań.');
        }
      } catch (err: any) {
        // Jeśli to błąd 404 od Next.js, pozwól mu działać
        if (err.digest === 'NEXT_NOT_FOUND') throw err;
        console.error(err);
        setAsyncError(err); // Wyślij resztę do error.tsx
      } finally {
        setIsLoading(false);
      }
    };
    fetchQuiz();
  }, [quizCode]);

  const handleReset = () => {
    const reshuffledQuestions = shuffleArray(questions);
    const fullyReshuffled = reshuffledQuestions.map((q) => ({
      ...q,
      answers: shuffleArray(q.answers)
    }));

    setIsStarted(false);
    setCurrentIdx(0);
    setQuestions(fullyReshuffled);
    setSelectedAnswers(fullyReshuffled.map((q) => ({ questionId: q.id, answerId: null })));
    setIsReviewingBeforeSubmit(false);
    setSubmissionResult(null);
    setShowResultReview(false);
  };

  const handleAnswerSelect = (answerId: number) => {
    const currentQuestionId = questions[currentIdx].id;
    setSelectedAnswers((prev) =>
      prev.map((ans) => (ans.questionId === currentQuestionId ? { ...ans, answerId: answerId } : ans))
    );
  };

  const handleNext = () => {
    if (currentIdx < questions.length - 1) {
      setCurrentIdx((c) => c + 1);
    } else {
      setIsReviewingBeforeSubmit(true);
    }
  };

  const handlePrev = () => {
    if (currentIdx > 0) {
      setCurrentIdx((c) => c - 1);
    }
  };

  const handleSubmitQuiz = async () => {
    if (!quizId || !studentName.trim()) {
      showToast('Proszę podać swoje imię przed wysłaniem!', 'info');
      return;
    }

    setIsSubmitting(true);
    try {
      const payload = {
        name: studentName.trim(),
        answers: selectedAnswers
          .filter((a) => a.answerId !== null)
          .map((a) => ({
            question: a.questionId,
            answer_id: a.answerId
          }))
      };

      const res = await fetch(`http://localhost:8000/api/quizes/${quizId}/submit/`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });

      if (res.status === 404) notFound();
      if (!res.ok) {
        const errData = await res.json();
        throw new Error(errData.detail || 'Wystąpił błąd podczas oceniania.');
      }

      const resultData: SubmissionResult = await res.json();
      setSubmissionResult(resultData);
    } catch (err: any) {
      if (err.digest === 'NEXT_NOT_FOUND') throw err;
      console.error(err);
      setAsyncError(err);
    } finally {
      setIsSubmitting(false);
    }
  };

  const toastOverlay = (
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
  );

  if (isLoading) {
    return (
      <div className="min-h-screen flex flex-col items-center justify-center bg-black text-yellow-400 font-black animate-pulse uppercase">
        Lazy Teacher wczytuje...
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen flex flex-col items-center justify-center bg-black p-4">
        <div className="bg-zinc-900 border border-red-500/50 p-6 sm:p-12 rounded-2xl sm:rounded-[2rem] text-center max-w-md">
          <h2 className="text-3xl font-black text-red-500 mb-4 uppercase">Błąd</h2>
          <p className="text-zinc-400 mb-8">{error}</p>
          <Link
            href="/"
            className="bg-zinc-800 text-white font-bold py-3 px-8 rounded-xl hover:bg-zinc-700 transition uppercase text-xs"
          >
            Powrót
          </Link>
        </div>
      </div>
    );
  }

  if (!isStarted) {
    const quizTopic = questions[0]?.topic || 'Ogólny';

    return (
      <div className="max-w-2xl mx-auto px-4 py-10 sm:py-20">
        {toastOverlay}
        <div className="bg-zinc-900 border-2 border-yellow-400/30 p-6 sm:p-12 rounded-2xl sm:rounded-[3rem] shadow-2xl text-center">
          <h1 className="text-3xl sm:text-5xl font-black text-white uppercase italic mb-6 tracking-tighter">
            quiz: <span className="text-yellow-400">"{quizTopic}"</span>
          </h1>

          <div className="mb-8 text-left">
            <label className="text-[10px] uppercase font-black tracking-widest text-zinc-500 mb-2 block pl-4">
              Twoje Imię
            </label>
            <input
              type="text"
              value={studentName}
              onChange={(e) => setStudentName(e.target.value)}
              placeholder="Jan Kowalski"
              className="w-full bg-zinc-950 border border-zinc-800 rounded-2xl px-6 py-4 text-white focus:outline-none focus:border-yellow-400"
            />
          </div>
          <button
            onClick={() => (studentName.trim() ? setIsStarted(true) : showToast('Podaj imię!', 'info'))}
            className="w-full py-6 bg-yellow-400 hover:bg-yellow-300 text-black font-black rounded-2xl border-b-8 border-yellow-600 uppercase tracking-widest transition-all"
          >
            Zacznij
          </button>
        </div>
      </div>
    );
  }

  if (submissionResult) {
    if (showResultReview) {
      return (
        <div className="max-w-4xl mx-auto px-4 py-12 animate-in fade-in duration-500">
          <div className="flex justify-between items-center mb-12">
            <h2 className="text-4xl font-black text-white uppercase italic tracking-tighter">Podsumowanie</h2>
            <button
              onClick={() => setShowResultReview(false)}
              className="bg-zinc-800 text-white font-black px-6 py-3 rounded-xl uppercase text-[11px] tracking-widest hover:bg-zinc-700 transition-all"
            >
              Wróć do wyniku
            </button>
          </div>
          <div className="space-y-8">
            {questions.map((q) => {
              const resultData = submissionResult.answers.find((a) => a.question_id === q.id);
              const isCorrectlyAnswered = resultData?.is_correct;

              return (
                <div
                  key={q.id}
                  className="bg-zinc-900 border border-zinc-800 p-5 sm:p-8 rounded-2xl sm:rounded-[2rem] shadow-xl"
                >
                  <div className="flex items-start justify-between gap-4 mb-6">
                    <p className="text-white text-xl font-bold leading-relaxed tracking-tight">{q.text}</p>
                    <div
                      className={`shrink-0 w-8 h-8 rounded flex items-center justify-center font-black ${isCorrectlyAnswered ? 'bg-green-500 text-black' : 'bg-red-500 text-white'}`}
                    >
                      {isCorrectlyAnswered ? '✓' : '✕'}
                    </div>
                  </div>

                  <div className="grid grid-cols-1 gap-3">
                    {q.answers.map((ans) => {
                      const isSelected = resultData?.selected_answer_id === ans.id;
                      const isActuallyCorrect = resultData?.correct_answer_id === ans.id;

                      let style = 'border-zinc-800 bg-zinc-950 text-zinc-500';
                      if (isActuallyCorrect) style = 'border-green-500 bg-green-500/10 text-green-400';
                      else if (isSelected && !isActuallyCorrect) style = 'border-red-500 bg-red-500/10 text-red-400';

                      return (
                        <div
                          key={ans.id}
                          className={`p-4 rounded-xl border-2 flex justify-between items-center ${style}`}
                        >
                          <span className="font-bold">{ans.text}</span>
                          {(isSelected || isActuallyCorrect) && (
                            <span className="text-xs uppercase tracking-widest font-black opacity-50">
                              {isActuallyCorrect ? 'Poprawna' : isSelected ? 'Twoja' : ''}
                            </span>
                          )}
                        </div>
                      );
                    })}
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      );
    }

    return (
      <div className="max-w-2xl mx-auto px-4 py-20 text-center text-white">
        <h1 className="text-4xl sm:text-6xl font-black mb-4 uppercase italic tracking-tighter">
          Wynik: {submissionResult.score}/{submissionResult.max_score}
        </h1>
        <p className="text-xl sm:text-2xl text-zinc-500 mb-10 font-bold uppercase tracking-widest">
          {submissionResult.percentage.toFixed(0)}%
        </p>

        <div className="flex flex-col gap-4">
          <button
            onClick={() => setShowResultReview(true)}
            className="text-yellow-400 hover:text-yellow-300 font-black uppercase text-xs tracking-widest underline decoration-2 underline-offset-8 mb-8"
          >
            Sprawdź błędy
          </button>

          <button
            onClick={handleReset}
            className="w-full py-5 bg-zinc-800 hover:bg-zinc-700 text-white font-black rounded-[2rem] uppercase tracking-widest transition-all border border-zinc-700 active:scale-95 mb-2"
          >
            Spróbuj ponownie
          </button>

          <Link
            href="/"
            className="bg-yellow-400 text-black px-12 py-5 rounded-[2rem] font-black uppercase tracking-widest border-b-8 border-yellow-600 active:scale-95 transition-all"
          >
            Koniec
          </Link>
        </div>
      </div>
    );
  }

  if (isReviewingBeforeSubmit) {
    const answeredCount = selectedAnswers.filter((a) => a.answerId !== null).length;

    return (
      <div className="max-w-2xl mx-auto px-4 py-20 animate-in fade-in zoom-in-95 duration-500">
        {toastOverlay}
        <div className="bg-zinc-900 border border-zinc-800 p-5 sm:p-10 rounded-2xl sm:rounded-[3rem] shadow-2xl text-center">
          <h2 className="text-2xl sm:text-4xl font-black text-white uppercase italic mb-8 tracking-tighter">
            Gotowy do wysłania?
          </h2>

          <div className="bg-zinc-950 rounded-2xl p-6 mb-10 border border-zinc-800">
            <p className="text-zinc-400 uppercase font-bold tracking-widest text-[10px] mb-2">Udzielono odpowiedzi:</p>
            <p
              className={`text-4xl font-black ${answeredCount === questions.length ? 'text-green-400' : 'text-yellow-400'}`}
            >
              {answeredCount} <span className="text-zinc-600 text-2xl">/ {questions.length}</span>
            </p>
          </div>

          <div className="grid grid-cols-2 gap-4">
            <button
              onClick={() => setIsReviewingBeforeSubmit(false)}
              className="py-4 bg-zinc-800 hover:bg-zinc-700 text-white font-black rounded-2xl uppercase tracking-widest text-[10px] transition-all"
              disabled={isSubmitting}
            >
              Wróć
            </button>
            <button
              onClick={handleSubmitQuiz}
              className="py-4 bg-yellow-400 hover:bg-yellow-300 text-black font-black rounded-2xl border-b-4 border-yellow-600 uppercase tracking-widest text-[10px] transition-all"
              disabled={isSubmitting}
            >
              {isSubmitting ? 'Wysyłanie...' : 'Zatwierdź odpowiedzi'}
            </button>
          </div>
        </div>
      </div>
    );
  }

  const currentQuestion = questions[currentIdx];
  const currentSelectedAnswer = selectedAnswers.find((a) => a.questionId === currentQuestion.id)?.answerId;

  return (
    <div className="max-w-4xl mx-auto px-4 py-12">
      <div className="w-full h-1 bg-zinc-800 rounded-full mb-10 overflow-hidden">
        <div
          className="h-full bg-yellow-400 transition-all duration-300"
          style={{ width: `${((currentIdx + 1) / questions.length) * 100}%` }}
        />
      </div>

      <div className="bg-zinc-900 border border-zinc-800 p-5 sm:p-16 rounded-2xl sm:rounded-[2.5rem] shadow-2xl relative">
        <h2 className="text-2xl sm:text-3xl font-black text-white text-center leading-relaxed mb-12 italic tracking-tight">
          {currentQuestion?.text}
        </h2>
        <div className="grid grid-cols-1 gap-3">
          {currentQuestion?.answers.map((ans) => {
            const isSelected = currentSelectedAnswer === ans.id;
            return (
              <button
                key={ans.id}
                onClick={() => handleAnswerSelect(ans.id)}
                className={`p-5 rounded-2xl border-2 font-bold text-lg transition-all text-left flex items-center justify-between group ${isSelected ? 'border-yellow-400 bg-yellow-400/10 text-yellow-400' : 'border-zinc-800 bg-zinc-950/40 text-zinc-400 hover:border-zinc-700'}`}
              >
                {ans.text}
                <div
                  className={`w-6 h-6 rounded-full border-2 flex items-center justify-center transition-all ${isSelected ? 'border-yellow-400 bg-yellow-400' : 'border-zinc-700 group-hover:border-zinc-500'}`}
                >
                  {isSelected && <div className="w-2.5 h-2.5 bg-black rounded-full"></div>}
                </div>
              </button>
            );
          })}
        </div>
      </div>
      <div className="flex justify-between mt-10 gap-4">
        <button
          onClick={handlePrev}
          disabled={currentIdx === 0}
          className="px-8 py-5 bg-zinc-800 text-white rounded-xl disabled:opacity-30 font-black uppercase text-[10px] tracking-widest transition-all"
        >
          Wstecz
        </button>
        <button
          onClick={handleNext}
          className="px-12 py-5 bg-yellow-400 text-black rounded-xl font-black border-b-4 border-yellow-600 uppercase text-[10px] tracking-widest active:scale-95 transition-all"
        >
          {currentIdx === questions.length - 1 ? 'Podsumowanie' : 'Dalej'}
        </button>
      </div>
    </div>
  );
}
