'use client';

import { useRouter, notFound } from 'next/navigation';
import { useEffect, useState, useCallback, use } from 'react';
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

interface ConfirmDialogState {
  open: boolean;
  title: string;
  message: string;
  onConfirm: () => void;
}

interface Toast {
  id: number;
  message: string;
  type: 'error' | 'info';
}

export default function QuizSetupPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = use(params);
  const { token, logout } = useAuth();
  const router = useRouter();

  const [isLoading, setIsLoading] = useState(true);
  const [questions, setQuestions] = useState<Question[]>([]);

  const [isSaving, setIsSaving] = useState(false);
  const [saveSuccess, setSaveSuccess] = useState(false);
  const [generatedLink, setGeneratedLink] = useState('');
  const [isLinking, setIsLinking] = useState(false);
  const [linkCopied, setLinkCopied] = useState(false);
  const [isActive, setIsActive] = useState<boolean | null>(null);
  const [isTogglingStatus, setIsTogglingStatus] = useState(false);
  const [isDeletingTest, setIsDeletingTest] = useState(false);

  const [asyncError, setAsyncError] = useState<Error | null>(null);

  // Confirm dialog state
  const [confirmDialog, setConfirmDialog] = useState<ConfirmDialogState>({
    open: false,
    title: '',
    message: '',
    onConfirm: () => {}
  });

  // Toast notifications
  const [toasts, setToasts] = useState<Toast[]>([]);

  if (asyncError) throw asyncError;

  const showToast = useCallback((message: string, type: 'error' | 'info' = 'error') => {
    const toastId = Date.now();
    setToasts((prev) => [...prev, { id: toastId, message, type }]);
    setTimeout(() => setToasts((prev) => prev.filter((t) => t.id !== toastId)), 4000);
  }, []);

  const showConfirm = useCallback((title: string, message: string, onConfirm: () => void) => {
    setConfirmDialog({ open: true, title, message, onConfirm });
  }, []);

  const closeConfirm = useCallback(() => {
    setConfirmDialog({ open: false, title: '', message: '', onConfirm: () => {} });
  }, []);

  const adjustHeight = (el: HTMLTextAreaElement | null) => {
    if (el) {
      el.style.height = 'auto';
      el.style.height = `${el.scrollHeight}px`;
    }
  };

  useEffect(() => {
    if (!localStorage.getItem('token')) {
      router.push('/login');
      return;
    }
    if (!token) return;

    const fetchTestData = async () => {
      try {
        const res = await fetch(`http://localhost:8000/api/tests/${id}/`, {
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
        if (!res.ok) throw new Error(`Błąd API: ${res.status}`);

        const data = await res.json();

        if (data.questions && Array.isArray(data.questions)) {
          setQuestions(data.questions);
        }

        // Set test status
        if (typeof data.is_active === 'boolean') {
          setIsActive(data.is_active);
        }

        // Fetch existing link
        if (data.code) {
          setGeneratedLink(`${window.location.origin}/start-quiz/${data.code}`);
        }

        setIsLoading(false);
      } catch (err: any) {
        if (err.digest === 'NEXT_NOT_FOUND') throw err;
        console.error(err);
        setAsyncError(err);
        setIsLoading(false);
      }
    };

    fetchTestData();
    // eslint-disable-next-line react-hooks/exhaustive-deps
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

  const handleDeleteQuestion = async (qIdx: number) => {
    const q = questions[qIdx];
    showConfirm('Usuń pytanie', `Czy na pewno chcesz usunąć pytanie #${qIdx + 1}?`, async () => {
      closeConfirm();
      try {
        const res = await fetch(`http://localhost:8000/api/tests/${id}/questions/${q.id}/`, {
          method: 'DELETE',
          headers: { Authorization: `Token ${token}` }
        });
        if (res.status === 401) {
          logout();
          return;
        }
        if (res.status === 404) notFound();
        if (!res.ok) {
          const data = await res.json().catch(() => ({}));
          showToast(data.message || 'Nie udało się usunąć pytania.');
          return;
        }
        setQuestions((prev) => prev.filter((_, i) => i !== qIdx));
      } catch (err: any) {
        if (err.digest === 'NEXT_NOT_FOUND') throw err;
        console.error(err);
        setAsyncError(err);
      }
    });
  };

  const handleDeleteAnswer = async (qIdx: number, oIdx: number) => {
    const q = questions[qIdx];
    const ans = q.answers[oIdx];
    if (q.answers.length <= 2) {
      showToast('Pytanie musi mieć co najmniej 2 odpowiedzi.', 'info');
      return;
    }
    showConfirm('Usuń odpowiedź', 'Czy na pewno chcesz usunąć tę odpowiedź?', async () => {
      closeConfirm();
      try {
        const res = await fetch(`http://localhost:8000/api/tests/${id}/questions/${q.id}/answers/${ans.id}/`, {
          method: 'DELETE',
          headers: { Authorization: `Token ${token}` }
        });
        if (res.status === 401) {
          logout();
          return;
        }
        if (res.status === 404) notFound();
        if (!res.ok) {
          const data = await res.json().catch(() => ({}));
          showToast(data.message || 'Nie udało się usunąć odpowiedzi.');
          return;
        }
        setQuestions((prev) => {
          const updated = [...prev];
          updated[qIdx] = { ...updated[qIdx], answers: updated[qIdx].answers.filter((_, i) => i !== oIdx) };
          return updated;
        });
      } catch (err: any) {
        if (err.digest === 'NEXT_NOT_FOUND') throw err;
        console.error(err);
        setAsyncError(err);
      }
    });
  };

  const handleToggleStatus = async () => {
    setIsTogglingStatus(true);
    try {
      const res = await fetch(`http://localhost:8000/api/tests/${id}/`, {
        method: 'PATCH',
        headers: {
          Authorization: `Token ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ is_active: !isActive })
      });
      if (res.status === 401) {
        logout();
        return;
      }
      if (res.status === 404) notFound();
      if (!res.ok) {
        const data = await res.json().catch(() => ({}));
        showToast(data.message || 'Nie udało się zmienić statusu testu.');
        return;
      }
      const data = await res.json();
      setIsActive(data.is_active);
    } catch (err: any) {
      if (err.digest === 'NEXT_NOT_FOUND') throw err;
      console.error(err);
      setAsyncError(err);
    } finally {
      setIsTogglingStatus(false);
    }
  };

  const handleDeleteTest = async () => {
    showConfirm('Usuń test', 'Czy na pewno chcesz usunąć ten test? Tej operacji nie można cofnąć.', async () => {
      closeConfirm();
      setIsDeletingTest(true);
      try {
        const res = await fetch(`http://localhost:8000/api/tests/${id}/`, {
          method: 'DELETE',
          headers: { Authorization: `Token ${token}` }
        });
        if (res.status === 401) {
          logout();
          return;
        }
        if (res.status === 404) notFound();
        if (!res.ok) {
          const data = await res.json().catch(() => ({}));
          showToast(data.message || 'Nie udało się usunąć testu.');
          return;
        }
        showToast('Test został usunięty.', 'info');
        setTimeout(() => router.push('/my-tests'), 1500);
      } catch (err: any) {
        if (err.digest === 'NEXT_NOT_FOUND') throw err;
        console.error(err);
        setAsyncError(err);
      } finally {
        setIsDeletingTest(false);
      }
    });
  };

  const handleSaveChanges = async () => {
    setIsSaving(true);
    try {
      const res = await fetch(`http://localhost:8000/api/tests/${id}/questions/`, {
        method: 'PATCH',
        headers: {
          Authorization: `Token ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ questions: questions })
      });

      if (res.status === 401) {
        logout();
        return;
      }
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
          Authorization: `Token ${token}`,
          'Content-Type': 'application/json'
        }
      });

      if (res.status === 401) {
        logout();
        return;
      }
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
    setLinkCopied(true);
    setTimeout(() => setLinkCopied(false), 2000);
  };

  if (isLoading) {
    return (
      <div className="min-h-[80vh] flex flex-col items-center justify-center p-4 bg-black">
        <div className="text-2xl font-black text-yellow-400 animate-pulse uppercase italic tracking-widest">
          Wczytywanie edytora...
        </div>
      </div>
    );
  }

  return (
    <>
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
            <div className="flex items-start gap-3">
              <div
                className={`w-8 h-8 rounded-lg flex items-center justify-center flex-shrink-0 ${toast.type === 'error' ? 'bg-red-500/20' : 'bg-yellow-400/20'}`}
              >
                {toast.type === 'error' ? (
                  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth="2"
                      d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L3.34 16.5c-.77.833.192 2.5 1.732 2.5z"
                    ></path>
                  </svg>
                ) : (
                  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth="2"
                      d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
                    ></path>
                  </svg>
                )}
              </div>
              <p className="text-sm font-bold leading-snug">{toast.message}</p>
            </div>
          </div>
        ))}
      </div>

      {/* Confirm dialog */}
      {confirmDialog.open && (
        <div className="fixed inset-0 z-[90] flex items-center justify-center p-4">
          <div className="absolute inset-0 bg-black/70 backdrop-blur-sm" onClick={closeConfirm}></div>
          <div className="relative bg-zinc-900 border-2 border-red-500/30 rounded-[2rem] p-8 max-w-md w-full shadow-2xl animate-in zoom-in-95 duration-200">
            <div className="flex items-center gap-4 mb-6">
              <div className="w-12 h-12 rounded-xl bg-red-500/20 flex items-center justify-center flex-shrink-0">
                <svg className="w-6 h-6 text-red-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth="2"
                    d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"
                  ></path>
                </svg>
              </div>
              <div>
                <h3 className="text-xl font-black text-white uppercase italic">{confirmDialog.title}</h3>
                <p className="text-zinc-400 text-sm font-medium mt-1">{confirmDialog.message}</p>
              </div>
            </div>
            <div className="flex gap-3">
              <button
                onClick={closeConfirm}
                className="flex-1 py-3 bg-zinc-800 hover:bg-zinc-700 text-zinc-300 font-bold rounded-xl transition-all text-sm uppercase tracking-wide"
              >
                Anuluj
              </button>
              <button
                onClick={confirmDialog.onConfirm}
                className="flex-1 py-3 bg-red-500 hover:bg-red-400 text-white font-black rounded-xl transition-all text-sm uppercase tracking-wide active:scale-95"
              >
                Usuń
              </button>
            </div>
          </div>
        </div>
      )}

      <div className="max-w-7xl mx-auto px-4 py-12 animate-in fade-in slide-in-from-bottom-4 duration-700">
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-10 items-start">
          <div className="lg:col-span-2 space-y-12">
            <h2 className="text-4xl font-black text-white uppercase italic tracking-tighter mb-4">Edycja Pytań</h2>

            {questions.map((q, qIdx) => (
              <div
                key={q.id || qIdx}
                className="bg-zinc-900 border border-zinc-800 p-10 rounded-[3rem] shadow-2xl hover:border-yellow-400/20 transition-all relative group/card"
              >
                <button
                  onClick={() => handleDeleteQuestion(qIdx)}
                  className="absolute top-6 right-6 w-10 h-10 rounded-xl bg-zinc-800 hover:bg-red-500/20 text-zinc-600 hover:text-red-400 flex items-center justify-center transition-all opacity-0 group-hover/card:opacity-100"
                  title="Usuń pytanie"
                >
                  <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth="2"
                      d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"
                    ></path>
                  </svg>
                </button>
                <div className="flex items-start gap-6 mb-12">
                  <div className="bg-yellow-400 text-black font-black w-14 h-14 flex-shrink-0 flex items-center justify-center rounded-[1.25rem] text-2xl shadow-lg">
                    {qIdx + 1}
                  </div>
                  <div className="flex-grow pt-1">
                    <label className="text-zinc-600 text-[11px] uppercase font-black tracking-[0.3em] mb-3 block">
                      Treść pytania
                    </label>
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
                    <div
                      key={ans.id || oIdx}
                      className={`p-5 rounded-[1.5rem] border-2 transition-all flex items-start gap-5 pr-8 group/ans ${ans.is_correct ? 'border-green-500 bg-green-500/5' : 'border-zinc-800 bg-zinc-950/50 hover:border-zinc-700'}`}
                    >
                      <button
                        onClick={() => setCorrectAnswer(qIdx, oIdx)}
                        className={`w-12 h-12 flex-shrink-0 rounded-2xl flex items-center justify-center transition-all ${ans.is_correct ? 'bg-green-500 text-black shadow-lg' : 'bg-zinc-800 text-zinc-600 hover:text-zinc-400'}`}
                      >
                        {ans.is_correct ? (
                          <span className="text-2xl font-bold">✓</span>
                        ) : (
                          <div className="w-3 h-3 rounded-full bg-zinc-700"></div>
                        )}
                      </button>
                      <textarea
                        value={ans.text}
                        onChange={(e) => updateOptionText(qIdx, oIdx, e.target.value)}
                        onInput={(e) => adjustHeight(e.target as HTMLTextAreaElement)}
                        className={`bg-transparent outline-none w-full py-3 font-bold text-lg transition-all resize-none overflow-hidden min-h-[40px] leading-relaxed ${ans.is_correct ? 'text-green-400' : 'text-zinc-400 focus:text-white'}`}
                        rows={1}
                      />
                      <button
                        onClick={() => handleDeleteAnswer(qIdx, oIdx)}
                        className="w-8 h-8 flex-shrink-0 rounded-lg bg-transparent hover:bg-red-500/20 text-zinc-700 hover:text-red-400 flex items-center justify-center transition-all opacity-0 group-hover/ans:opacity-100 self-center"
                        title="Usuń odpowiedź"
                      >
                        <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path
                            strokeLinecap="round"
                            strokeLinejoin="round"
                            strokeWidth="2"
                            d="M6 18L18 6M6 6l12 12"
                          ></path>
                        </svg>
                      </button>
                    </div>
                  ))}
                </div>
              </div>
            ))}
          </div>

          <div className="sticky top-12 mt-14 space-y-6 max-h-[calc(100vh-100px)] overflow-y-auto hide-scrollbar">
            {/* Status panel */}
            {isActive !== null && (
              <div className="bg-zinc-900 border border-zinc-800 px-5 py-4 rounded-2xl flex items-center justify-between gap-4">
                <div className="flex items-center gap-3 min-w-0">
                  <span
                    className={`w-2.5 h-2.5 rounded-full flex-shrink-0 ${isActive ? 'bg-green-500 animate-pulse' : 'bg-red-500'}`}
                  ></span>
                  <span className="text-sm font-bold text-white truncate">{isActive ? 'Aktywny' : 'Nieaktywny'}</span>
                </div>
                <button
                  onClick={handleToggleStatus}
                  disabled={isTogglingStatus}
                  className={`px-4 py-2 text-xs font-black rounded-xl transition-all active:scale-95 uppercase tracking-wider disabled:opacity-50 flex-shrink-0 ${isActive ? 'bg-zinc-800 hover:bg-red-500/20 text-zinc-400 hover:text-red-400' : 'bg-green-500/10 hover:bg-green-500/20 text-green-400'}`}
                >
                  {isTogglingStatus ? '...' : isActive ? 'Dezaktywuj' : 'Aktywuj'}
                </button>
              </div>
            )}
            {/* Link panel - always visible if link exists */}
            {generatedLink && (
              <div className="bg-zinc-900 border-2 border-yellow-400/30 p-6 rounded-[2rem] shadow-2xl animate-in fade-in duration-500">
                <div className="flex items-center gap-3 mb-4">
                  <div className="w-10 h-10 bg-yellow-400/10 rounded-xl flex items-center justify-center text-yellow-400">
                    <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path
                        strokeLinecap="round"
                        strokeLinejoin="round"
                        strokeWidth="2"
                        d="M13.828 10.172a4 4 0 00-5.656 0l-4 4a4 4 0 105.656 5.656l1.102-1.101m-.758-4.899a4 4 0 005.656 0l4-4a4 4 0 00-5.656-5.656l-1.1 1.1"
                      ></path>
                    </svg>
                  </div>
                  <h4 className="text-sm font-black text-white uppercase italic tracking-tight">Link do testu</h4>
                </div>
                <div className="bg-zinc-950 border border-yellow-400/20 p-3 rounded-xl mb-3">
                  <a
                    href={generatedLink}
                    target="_blank"
                    className="text-yellow-400 font-bold text-xs break-all hover:underline block"
                  >
                    {generatedLink}
                  </a>
                </div>
                <button
                  onClick={copyToClipboard}
                  className={`w-full py-3 font-black rounded-xl transition-all active:scale-95 text-sm uppercase tracking-widest ${linkCopied ? 'bg-green-500/20 text-green-400 border border-green-500/30' : 'bg-yellow-400/10 hover:bg-yellow-400/20 text-yellow-400 border border-yellow-400/20'}`}
                >
                  {linkCopied ? 'Skopiowano!' : 'Kopiuj link'}
                </button>
              </div>
            )}

            {/* Action panel */}
            <div className="bg-zinc-900 border-2 border-yellow-400/30 p-6 sm:p-8 rounded-[2rem] shadow-2xl flex flex-col items-center text-center relative overflow-hidden">
              <div className="w-14 h-14 bg-yellow-400/10 rounded-2xl flex items-center justify-center mb-5 text-yellow-400 shadow-inner">
                <svg className="w-7 h-7" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth="2.5"
                    d="M8 7H5a2 2 0 00-2 2v9a2 2 0 002 2h14a2 2 0 002-2V9a2 2 0 00-2-2h-3m-1 4l-3 3m0 0l-3-3m3 3V4"
                  ></path>
                </svg>
              </div>

              <h3 className="text-2xl font-black text-white mb-2 uppercase italic">Panel Akcji</h3>
              <p className="text-zinc-500 mb-6 text-xs leading-relaxed font-medium">
                Zatwierdź zmiany w treści pytań przed wygenerowaniem linku dla uczniów.
              </p>

              <div className="flex flex-col gap-4 w-full">
                <button
                  onClick={handleSaveChanges}
                  disabled={isSaving || saveSuccess}
                  className={`w-full py-4 text-black font-black rounded-xl transition-all active:scale-95 uppercase tracking-widest border-b-4 disabled:opacity-50 shadow-lg text-sm ${saveSuccess ? 'bg-green-400 border-green-600' : 'bg-green-500 hover:bg-green-400 border-green-700'}`}
                >
                  {isSaving ? 'Zapisywanie...' : saveSuccess ? 'Zapisano!' : 'Zatwierdź zmiany'}
                </button>

                <div className="h-px bg-zinc-800 w-full my-2"></div>
                <button
                  onClick={handleGenerateLink}
                  disabled={isLinking}
                  className="w-full py-4 bg-yellow-400 hover:bg-yellow-300 text-black font-black rounded-xl transition-all active:scale-95 uppercase tracking-widest shadow-[0_20px_50px_rgba(250,204,21,0.15)] border-b-4 border-yellow-600 disabled:opacity-50 text-sm"
                >
                  {isLinking ? 'Generowanie...' : generatedLink ? 'Generuj nowy link' : 'Generuj Link'}
                </button>

                <div className="h-px bg-zinc-800 w-full my-4"></div>
                <button
                  onClick={handleDeleteTest}
                  disabled={isDeletingTest}
                  className="w-full py-3 bg-red-600 hover:bg-red-500 text-white font-black rounded-xl transition-all active:scale-95 uppercase tracking-widest border-b-4 border-red-700 disabled:opacity-50 text-sm shadow-lg"
                >
                  {isDeletingTest ? 'Usuwanie...' : 'Usuń test'}
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>
    </>
  );
}
