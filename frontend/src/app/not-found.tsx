'use client';

import Link from 'next/link';

export default function NotFound() {
  return (
    <div className="min-h-[80vh] flex flex-col items-center justify-center px-4 text-center">
      <div className="relative">
        <h1 className="text-[12rem] md:text-[18rem] font-black text-zinc-900 leading-none select-none">
          404
        </h1>
        <div className="absolute inset-0 flex flex-col items-center justify-center">
          <span className="text-4xl md:text-6xl font-black text-yellow-400 uppercase italic tracking-tighter drop-shadow-2xl">
            Zgubiłeś się?
          </span>
        </div>
      </div>
      
      <p className="max-w-md text-zinc-500 text-lg md:text-xl font-medium mt-4 mb-12 leading-relaxed">
        Nawet <span className="text-white">Lazy Teacher</span> nie potrafi znaleźć tej strony. Prawdopodobnie poszła na wagary.
      </p>

      <Link 
        href="/"
        className="group relative px-12 py-5 bg-yellow-400 text-black font-black rounded-2xl uppercase tracking-widest text-sm transition-all hover:scale-105 active:scale-95 shadow-[0_20px_50px_rgba(250,204,21,0.2)]"
      >
        <span className="relative z-10">Wróć do bazy</span>
        <div className="absolute inset-0 bg-white rounded-2xl scale-0 group-hover:scale-100 transition-transform duration-300 opacity-20"></div>
      </Link>
      
      <div className="mt-20 grid grid-cols-3 gap-4 opacity-20">
        {[...Array(3)].map((_, i) => (
          <div key={i} className="w-2 h-2 bg-yellow-400 rounded-full animate-bounce" style={{ animationDelay: `${i * 0.2}s` }}></div>
        ))}
      </div>
    </div>
  );
}