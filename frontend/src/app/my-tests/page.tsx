'use client';

import { useEffect, useState } from 'react';
import { useAuth } from '@/context/AuthContext';
import { useRouter } from 'next/navigation';
import Link from 'next/link';

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

interface TestItem {
  id: number;
  code: string;
  document_id: number;
  is_active: boolean;
  questions: Question[];
  created_at: string;
}

interface SubmittedAnswer {
  question_id: number;
  selected_answer_id: number | null;
  is_correct: boolean;
  question_text: string;
  selected_answer_text: string | null;
  correct_answer_id: number;
}

interface Submission {
  id: number;
  student_name: string;
  score: number;
  max_score: number;
  percentage: number;
  passed: boolean;
  submitted_at: string;
  answers: SubmittedAnswer[];
}

export default function MyTestsPage() {
  const { token, logout } = useAuth();
  const router = useRouter();

  const [tests, setTests] = useState<TestItem[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [expandedTest, setExpandedTest] = useState<number | null>(null);
  const [submissions, setSubmissions] = useState<Record<number, Submission[]>>({});
  const [loadingSubmissions, setLoadingSubmissions] = useState<number | null>(null);
  const [copiedTestId, setCopiedTestId] = useState<number | null>(null);
  const [docTitles, setDocTitles] = useState<Record<number, string>>({});
  const [downloadingDocId, setDownloadingDocId] = useState<number | null>(null);

  useEffect(() => {
    if (!localStorage.getItem('token')) {
      router.push('/login');
      return;
    }
    if (!token) return;

    const fetchTests = async () => {
      try {
        const res = await fetch('http://localhost:8000/api/tests/', {
          headers: {
            Authorization: `Token ${token}`,
            'Content-Type': 'application/json'
          }
        });
        if (res.status === 401) {
          logout();
          return;
        }
        if (!res.ok) throw new Error('Błąd pobierania testów.');
        const data = await res.json();
        setTests(data);

        // Fetch document titles for all tests
        const uniqueDocIds = [...new Set(data.map((t: TestItem) => t.document_id))] as number[];
        const docTitlesMap: Record<number, string> = {};

        for (const docId of uniqueDocIds) {
          try {
            const docRes = await fetch(`http://localhost:8000/api/documents/${docId}/`, {
              headers: {
                Authorization: `Token ${token}`,
                'Content-Type': 'application/json'
              }
            });
            if (docRes.ok) {
              const docData = await docRes.json();
              docTitlesMap[docId] = docData.title;
            }
          } catch (err) {
            console.error(`Błąd pobierania dokumentu ${docId}:`, err);
          }
        }
        setDocTitles(docTitlesMap);
      } catch (err) {
        console.error(err);
      } finally {
        setIsLoading(false);
      }
    };

    fetchTests();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [token]);

  const toggleSubmissions = async (testId: number) => {
    if (expandedTest === testId) {
      setExpandedTest(null);
      return;
    }

    setExpandedTest(testId);

    if (submissions[testId]) return;

    setLoadingSubmissions(testId);
    try {
      const res = await fetch(`http://localhost:8000/api/tests/${testId}/submissions/`, {
        headers: {
          Authorization: `Token ${token}`,
          'Content-Type': 'application/json'
        }
      });
      if (res.status === 401) {
        logout();
        return;
      }
      if (!res.ok) throw new Error('Błąd pobierania wyników.');
      const data: Submission[] = await res.json();
      setSubmissions((prev) => ({ ...prev, [testId]: data }));
    } catch (err) {
      console.error(err);
    } finally {
      setLoadingSubmissions(null);
    }
  };

  const copyTestLink = (test: TestItem) => {
    const link = `${window.location.origin}/start-quiz/${test.code}`;
    navigator.clipboard.writeText(link);
    setCopiedTestId(test.id);
    setTimeout(() => setCopiedTestId(null), 2000);
  };

  const handleDownloadDocument = async (docId: number) => {
    setDownloadingDocId(docId);
    try {
      const res = await fetch(`http://localhost:8000/api/documents/${docId}/download-url/`, {
        method: 'GET',
        headers: {
          Authorization: `Token ${token}`,
          'Content-Type': 'application/json'
        }
      });

      if (!res.ok) throw new Error('Nie udało się wygenerować linku do pliku.');

      const data = await res.json();
      if (data.url) {
        window.open(data.url, '_blank');
      }
    } catch (err) {
      console.error(err);
    } finally {
      setDownloadingDocId(null);
    }
  };

  if (isLoading) {
    return (
      <div className="min-h-[80vh] flex flex-col items-center justify-center p-4 bg-black">
        <div className="text-2xl font-black text-yellow-400 animate-pulse uppercase italic tracking-widest">
          Wczytywanie testów...
        </div>
      </div>
    );
  }

  return (
    <div className="max-w-5xl mx-auto px-4 py-12 animate-in fade-in slide-in-from-bottom-4 duration-700">
      <h1 className="text-4xl font-black text-yellow-400 uppercase italic tracking-tighter mb-12 text-center">
        Moje Testy
      </h1>

      {tests.length === 0 ? (
        <div className="text-center py-20">
          <div className="text-6xl mb-6">📝</div>
          <p className="text-zinc-500 text-lg font-medium mb-6">Nie masz jeszcze żadnych testów.</p>
          <Link
            href="/upload"
            className="bg-yellow-400 hover:bg-yellow-300 text-black font-black px-8 py-4 rounded-xl transition-all active:scale-95 uppercase tracking-widest shadow-lg inline-block"
          >
            Wgraj materiały
          </Link>
        </div>
      ) : (
        <div className="space-y-6">
          {tests.map((test) => {
            const testSubmissions = submissions[test.id];
            const isExpanded = expandedTest === test.id;
            const isLoadingSubs = loadingSubmissions === test.id;

            return (
              <div
                key={test.id}
                className="bg-zinc-900 border border-zinc-800 rounded-xl sm:rounded-[2rem] shadow-2xl overflow-hidden hover:border-yellow-400/20 transition-all"
              >
                {/* Test Header */}
                <div className="p-4 sm:p-8">
                  <div className="flex flex-col sm:flex-row sm:items-center gap-4 mb-4">
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-3 mb-2">
                        <h2 className="text-xl md:text-2xl font-black text-white uppercase italic tracking-tight truncate">
                          {test.questions[0]?.topic || test.code}
                        </h2>
                        <span
                          className={`px-3 py-1 rounded-full text-[10px] font-black uppercase tracking-widest ${test.is_active ? 'bg-green-500/20 text-green-400' : 'bg-zinc-700/50 text-zinc-500'}`}
                        >
                          {test.is_active ? 'Aktywny' : 'Nieaktywny'}
                        </span>
                      </div>
                      <div className="flex items-center gap-4 text-zinc-500 text-sm font-medium">
                        <span>{test.questions.length} pytań</span>
                        <span>•</span>
                        <span>{new Date(test.created_at).toLocaleDateString('pl-PL')}</span>
                      </div>
                    </div>

                    <div className="flex items-center gap-3 flex-shrink-0">
                      <Link
                        href={`/quiz-setup/${test.id}`}
                        className="px-5 py-3 bg-zinc-800 hover:bg-zinc-700 text-zinc-300 font-bold rounded-xl transition-all text-sm uppercase tracking-wide"
                      >
                        Edytuj
                      </Link>
                      <button
                        onClick={() => toggleSubmissions(test.id)}
                        className={`px-5 py-3 font-bold rounded-xl transition-all text-sm uppercase tracking-wide ${isExpanded ? 'bg-yellow-400 text-black' : 'bg-yellow-400/10 hover:bg-yellow-400/20 text-yellow-400'}`}
                      >
                        {isExpanded ? 'Ukryj wyniki' : 'Wyniki'}
                      </button>
                    </div>
                  </div>

                  {/* Document and Link sections */}
                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 mt-6 pt-6 border-t border-zinc-800">
                    {/* Document section */}
                    {docTitles[test.document_id] && (
                      <div className="flex items-center justify-between gap-3 p-4 bg-green-500/5 border border-green-500/30 rounded-xl">
                        <div className="flex items-center gap-3 min-w-0">
                          <svg
                            className="w-5 h-5 text-green-400 flex-shrink-0"
                            fill="none"
                            stroke="currentColor"
                            viewBox="0 0 24 24"
                          >
                            <path
                              strokeLinecap="round"
                              strokeLinejoin="round"
                              strokeWidth="2"
                              d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"
                            ></path>
                          </svg>
                          <div className="min-w-0">
                            <p className="text-xs text-zinc-500 font-medium">Dokument</p>
                            <p className="text-sm font-bold text-green-400 truncate">{docTitles[test.document_id]}</p>
                          </div>
                        </div>
                        <button
                          onClick={() => handleDownloadDocument(test.document_id)}
                          disabled={downloadingDocId === test.document_id}
                          className="flex-shrink-0 text-green-400 hover:text-green-300 transition-colors disabled:opacity-50"
                          title="Pobierz dokument"
                        >
                          {downloadingDocId === test.document_id ? (
                            <svg className="w-5 h-5 animate-spin" fill="none" viewBox="0 0 24 24">
                              <circle
                                className="opacity-25"
                                cx="12"
                                cy="12"
                                r="10"
                                stroke="currentColor"
                                strokeWidth="4"
                              ></circle>
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
                                d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4"
                              ></path>
                            </svg>
                          )}
                        </button>
                      </div>
                    )}

                    {/* Test link section */}
                    <div className="flex items-center justify-between gap-3 p-4 bg-yellow-400/5 border border-yellow-400/30 rounded-xl">
                      <div className="flex items-center gap-3 min-w-0">
                        <svg
                          className="w-5 h-5 text-yellow-400 flex-shrink-0"
                          fill="none"
                          stroke="currentColor"
                          viewBox="0 0 24 24"
                        >
                          <path
                            strokeLinecap="round"
                            strokeLinejoin="round"
                            strokeWidth="2"
                            d="M13.828 10.172a4 4 0 00-5.656 0l-4 4a4 4 0 105.656 5.656l1.102-1.101m-.758-4.899a4 4 0 005.656 0l4-4a4 4 0 00-5.656-5.656l-1.1 1.1"
                          ></path>
                        </svg>
                        <div className="min-w-0">
                          <p className="text-xs text-zinc-500 font-medium">Link do testu</p>
                          <a
                            href={`${typeof window !== 'undefined' ? window.location.origin : ''}/start-quiz/${test.code}`}
                            target="_blank"
                            className="text-sm font-bold text-yellow-400 hover:text-yellow-300 truncate"
                            title="Otwórz test"
                          >
                            {test.code}
                          </a>
                        </div>
                      </div>
                      <button
                        onClick={() => copyTestLink(test)}
                        className={`flex-shrink-0 transition-colors ${copiedTestId === test.id ? 'text-green-400' : 'text-yellow-400 hover:text-yellow-300'}`}
                        title={copiedTestId === test.id ? 'Skopiowano!' : 'Kopiuj link'}
                      >
                        {copiedTestId === test.id ? (
                          <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path
                              strokeLinecap="round"
                              strokeLinejoin="round"
                              strokeWidth="2"
                              d="M5 13l4 4L19 7"
                            ></path>
                          </svg>
                        ) : (
                          <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path
                              strokeLinecap="round"
                              strokeLinejoin="round"
                              strokeWidth="2"
                              d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z"
                            ></path>
                          </svg>
                        )}
                      </button>
                    </div>
                  </div>
                </div>

                {/* Submissions Panel */}
                {isExpanded && (
                    <div className="border-t border-zinc-800 bg-zinc-950/50 p-4 sm:p-8 animate-in slide-in-from-top-2 duration-300">
                    {isLoadingSubs ? (
                      <p className="text-yellow-400 font-bold animate-pulse text-center py-4 uppercase tracking-widest text-sm">
                        Ładowanie wyników...
                      </p>
                    ) : !testSubmissions || testSubmissions.length === 0 ? (
                      <p className="text-zinc-600 text-center py-4 font-medium">
                        Nikt jeszcze nie rozwiązał tego testu.
                      </p>
                    ) : (
                      <div>
                        <div className="flex items-center justify-between mb-6">
                          <h3 className="text-lg font-black text-white uppercase italic tracking-tight">
                            Wyniki ({testSubmissions.length})
                          </h3>
                        </div>
                        <div className="space-y-3">
                          {testSubmissions.map((sub) => (
                            <div
                              key={sub.id}
                              className={`flex flex-col sm:flex-row sm:items-center gap-3 p-5 rounded-2xl border transition-all ${sub.passed ? 'border-green-500/30 bg-green-500/5' : 'border-red-500/30 bg-red-500/5'}`}
                            >
                              <div className="flex-1 min-w-0">
                                <p className="text-white font-bold text-lg truncate">{sub.student_name}</p>
                                <p className="text-zinc-500 text-xs font-medium mt-1">
                                  {new Date(sub.submitted_at).toLocaleString('pl-PL')}
                                </p>
                              </div>
                              <div className="flex items-center gap-4">
                                <div className="text-right">
                                  <p
                                    className={`text-2xl font-black ${sub.passed ? 'text-green-400' : 'text-red-400'}`}
                                  >
                                    {sub.score}/{sub.max_score}
                                  </p>
                                  <p className="text-zinc-500 text-[10px] font-black uppercase tracking-widest">
                                    {sub.percentage.toFixed(0)}%
                                  </p>
                                </div>
                                <div
                                  className={`w-12 h-12 rounded-xl flex items-center justify-center font-black text-lg ${sub.passed ? 'bg-green-500/20 text-green-400' : 'bg-red-500/20 text-red-400'}`}
                                >
                                  {sub.passed ? '✓' : '✗'}
                                </div>
                              </div>
                            </div>
                          ))}
                        </div>
                      </div>
                    )}
                  </div>
                )}
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
