import type { Metadata } from 'next';
import { Inter } from 'next/font/google';
import './globals.css';
import { AuthProvider } from '@/context/AuthContext';
import Header from '@/components/Header';

const inter = Inter({ subsets: ['latin'] });

export const metadata: Metadata = {
  title: 'LazyTeacher - Quizy z Notatek',
  description: 'Generuj quizy ze swoich notatek PDF'
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="pl">
      <body className={`${inter.className} bg-slate-50 min-h-screen`}>
        <AuthProvider>
          <Header />
          <main className="pt-20 sm:pt-24 min-h-screen">{children}</main>
        </AuthProvider>
      </body>
    </html>
  );
}
