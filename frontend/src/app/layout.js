import './global.css';
import Link from 'next/link';
import { MessageSquare } from 'lucide-react';
import Sidebar from './components/sidebar';

export const metadata = {
  title: 'AI Dubbing Studio',
  description: 'Route-based dubbing dashboard for uploads, jobs, and history.',
};

export default function RootLayout({ children }) {
  return (
    <html lang="en" suppressHydrationWarning>
      <body className="bg-slate-50 text-slate-900 antialiased" suppressHydrationWarning>
        <div className="flex min-h-screen">
          <Sidebar />
          <div className="flex-1 lg:pl-64">
            <main className="min-h-screen">{children}</main>
          </div>
          <Link
            href="/feedback"
            className="fixed bottom-4 right-4 z-20 inline-flex items-center gap-2 rounded-full bg-slate-900 px-4 py-2.5 text-sm font-medium text-white shadow-lg shadow-slate-900/20 transition hover:bg-slate-700 lg:hidden"
          >
            <MessageSquare className="h-4 w-4" />
            Feedback
          </Link>
        </div>
      </body>
    </html>
  );
}
