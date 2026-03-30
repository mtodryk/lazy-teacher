'use client';

import { useState, useEffect, useRef, useCallback } from 'react';

import { API_BASE_URL } from '@/lib/api';

interface ChatMessage {
  role: 'user' | 'assistant';
  content: string;
  created_at?: string;
}

interface AiChatModalProps {
  isOpen: boolean;
  onClose: () => void;
  quizId: number;
  questionId: number;
  questionText: string;
  correctAnswerText: string;
  token: string;
}

const MAX_MESSAGES = 20;

export default function AiChatModal({
  isOpen,
  onClose,
  quizId,
  questionId,
  questionText,
  correctAnswerText,
  token
}: AiChatModalProps) {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [isInitializing, setIsInitializing] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const getHeaders = useCallback(
    () => ({
      Authorization: `Token ${token}`,
      'Content-Type': 'application/json'
    }),
    [token]
  );

  const getChatUrl = useCallback(
    () => `${API_BASE_URL}/api/quizes/${quizId}/questions/${questionId}/chat/`,
    [quizId, questionId]
  );

  const pollTask = useCallback(
    async (taskId: string) => {
      const hdrs = getHeaders();
      const poll = async (): Promise<ChatMessage[]> => {
        const res = await fetch(`${API_BASE_URL}/api/quizes/chat-task/${taskId}/`, { headers: hdrs });
        if (!res.ok) throw new Error('Poll failed');
        const data = await res.json();
        if (data.status === 'SUCCESS') return data.messages || [];
        if (data.status === 'FAILURE') throw new Error('Task failed');
        await new Promise((r) => setTimeout(r, 1500));
        return poll();
      };
      return poll();
    },
    [getHeaders]
  );

  useEffect(() => {
    if (!isOpen) return;

    const initChat = async () => {
      setIsInitializing(true);
      const url = getChatUrl();
      const hdrs = getHeaders();
      try {
        // Try to get existing chat history
        const res = await fetch(url, { headers: hdrs });
        if (res.ok) {
          const data = await res.json();
          if (data.messages && data.messages.length > 0) {
            setMessages(data.messages);
            setIsInitializing(false);
            return;
          }
        }

        // No existing chat — create one (POST triggers async explanation generation)
        const createRes = await fetch(url, {
          method: 'POST',
          headers: hdrs,
          body: JSON.stringify({})
        });

        if (createRes.ok) {
          const data = await createRes.json();
          if (data.task_id) {
            const msgs = await pollTask(data.task_id);
            setMessages(msgs);
          } else if (data.messages) {
            setMessages(data.messages);
          }
        }
      } catch (err) {
        console.error('Failed to init chat:', err);
      } finally {
        setIsInitializing(false);
      }
    };

    setMessages([]);
    initChat();
  }, [isOpen, quizId, questionId, token, getChatUrl, getHeaders, pollTask]);

  const handleSend = async () => {
    if (!input.trim() || isLoading) return;

    const userMessage = input.trim();
    setInput('');
    setMessages((prev) => [...prev, { role: 'user', content: userMessage }]);
    setIsLoading(true);

    try {
      const res = await fetch(getChatUrl(), {
        method: 'POST',
        headers: getHeaders(),
        body: JSON.stringify({ message: userMessage })
      });

      if (res.ok) {
        const data = await res.json();
        if (data.task_id) {
          const msgs = await pollTask(data.task_id);
          setMessages(msgs);
        } else if (data.messages) {
          setMessages(data.messages);
        }
      } else {
        const err = await res.json().catch(() => null);
        if (err?.message) {
          setMessages((prev) => [...prev, { role: 'assistant', content: `⚠️ ${err.message}` }]);
        }
      }
    } catch (err) {
      console.error('Failed to send message:', err);
    } finally {
      setIsLoading(false);
    }
  };

  const handleClearChat = async () => {
    try {
      const res = await fetch(getChatUrl(), {
        method: 'DELETE',
        headers: getHeaders()
      });

      if (res.ok) {
        const data = await res.json();
        setMessages(data.messages || []);
      }
    } catch (err) {
      console.error('Failed to clear chat:', err);
    }
  };

  const isAtLimit = messages.length >= MAX_MESSAGES;

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/80 backdrop-blur-sm p-4 animate-in fade-in duration-200">
      <div className="bg-zinc-900 border border-zinc-800 rounded-2xl sm:rounded-[2.5rem] w-full max-w-2xl shadow-2xl flex flex-col max-h-[85vh]">
        {/* Header */}
        <div className="flex justify-between items-center p-5 sm:p-6 border-b border-zinc-800">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 bg-yellow-400/10 rounded-xl flex items-center justify-center">
              <svg className="w-5 h-5 text-yellow-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth="2"
                  d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z"
                ></path>
              </svg>
            </div>
            <div>
              <h2 className="text-lg font-black text-white uppercase tracking-tight">AI Wyjaśnienie</h2>
              <p className="text-zinc-500 text-xs truncate max-w-[300px]">{questionText}</p>
            </div>
          </div>
          <div className="flex items-center gap-2">
            {messages.length > 1 && (
              <button
                onClick={handleClearChat}
                title="Wyczyść czat"
                className="text-zinc-500 hover:text-yellow-400 transition-colors bg-zinc-800/50 hover:bg-zinc-800 p-2 rounded-full"
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
            )}
            <button
              onClick={onClose}
              className="text-zinc-500 hover:text-white transition-colors bg-zinc-800/50 hover:bg-zinc-800 p-2 rounded-full"
            >
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2.5" d="M6 18L18 6M6 6l12 12"></path>
              </svg>
            </button>
          </div>
        </div>

        {/* Correct answer badge */}
        <div className="px-5 sm:px-6 pt-4">
          <div className="inline-flex items-center gap-2 px-3 py-1.5 rounded-full bg-green-500/10 border border-green-500/20 text-green-400 text-xs font-bold">
            <span className="w-1.5 h-1.5 bg-green-500 rounded-full"></span>
            Poprawna: {correctAnswerText}
          </div>
        </div>

        {/* Messages */}
        <div className="flex-1 overflow-y-auto p-5 sm:p-6 space-y-4 min-h-[200px]">
          {isInitializing ? (
            <div className="flex flex-col items-center justify-center h-full gap-3 py-10">
              <div className="relative w-12 h-12">
                <div className="absolute inset-0 rounded-full border-4 border-yellow-400/20"></div>
                <div className="absolute inset-0 rounded-full border-4 border-transparent border-t-yellow-400 animate-spin"></div>
              </div>
              <p className="text-yellow-400 text-sm font-bold animate-pulse uppercase tracking-wider">
                AI analizuje...
              </p>
            </div>
          ) : (
            messages.map((msg, idx) => (
              <div key={idx} className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}>
                <div
                  className={`max-w-[80%] p-4 rounded-2xl text-sm leading-relaxed ${
                    msg.role === 'user'
                      ? 'bg-yellow-400/10 border border-yellow-400/30 text-yellow-100'
                      : 'bg-zinc-800/50 border border-zinc-700/50 text-zinc-200'
                  }`}
                >
                  {msg.role === 'assistant' && (
                    <div className="flex items-center gap-1.5 mb-2">
                      <svg
                        className="w-3.5 h-3.5 text-yellow-400"
                        fill="none"
                        stroke="currentColor"
                        viewBox="0 0 24 24"
                      >
                        <path
                          strokeLinecap="round"
                          strokeLinejoin="round"
                          strokeWidth="2"
                          d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z"
                        ></path>
                      </svg>
                      <span className="text-[10px] uppercase font-black tracking-widest text-yellow-400/60">
                        AI Nauczyciel
                      </span>
                    </div>
                  )}
                  <p className="whitespace-pre-wrap">{msg.content}</p>
                </div>
              </div>
            ))
          )}
          {isLoading && (
            <div className="flex justify-start">
              <div className="bg-zinc-800/50 border border-zinc-700/50 p-4 rounded-2xl">
                <div className="flex gap-1.5">
                  <div
                    className="w-2 h-2 bg-yellow-400/60 rounded-full animate-bounce"
                    style={{ animationDelay: '0ms' }}
                  ></div>
                  <div
                    className="w-2 h-2 bg-yellow-400/60 rounded-full animate-bounce"
                    style={{ animationDelay: '150ms' }}
                  ></div>
                  <div
                    className="w-2 h-2 bg-yellow-400/60 rounded-full animate-bounce"
                    style={{ animationDelay: '300ms' }}
                  ></div>
                </div>
              </div>
            </div>
          )}
          <div ref={messagesEndRef} />
        </div>

        {/* Input */}
        <div className="p-5 sm:p-6 border-t border-zinc-800">
          {isAtLimit ? (
            <p className="text-center text-zinc-500 text-xs font-bold uppercase tracking-wider">
              Osiągnięto limit wiadomości ({MAX_MESSAGES}). Wyczyść czat, aby kontynuować.
            </p>
          ) : (
            <div className="flex gap-3">
              <input
                type="text"
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyDown={(e) => e.key === 'Enter' && handleSend()}
                placeholder="Zadaj pytanie..."
                disabled={isLoading || isInitializing}
                className="flex-1 bg-zinc-800 border border-zinc-700 rounded-xl px-4 py-3 text-white text-sm focus:outline-none focus:border-yellow-400/50 transition-colors disabled:opacity-50"
              />
              <button
                onClick={handleSend}
                disabled={isLoading || isInitializing || !input.trim()}
                className="bg-yellow-400 hover:bg-yellow-300 text-black font-black px-6 rounded-xl transition-all active:scale-95 disabled:opacity-50 disabled:cursor-not-allowed uppercase text-xs tracking-wider"
              >
                Wyślij
              </button>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
