'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { MessageSquare } from 'lucide-react';
import Sidebar from './sidebar';

const studioRoots = ['/dashboard', '/dubbing', '/history', '/feedback'];

export default function AppShell({ children }) {
  const pathname = usePathname();
  const isStudioRoute = studioRoots.some((root) => pathname === root || pathname.startsWith(`${root}/`));

  return (
    <div className="flex min-h-screen">
      {isStudioRoute && <Sidebar />}
      <div className={`flex-1 ${isStudioRoute ? 'lg:pl-64' : ''}`}>
        <main className="min-h-screen">{children}</main>
      </div>
      {isStudioRoute && (
        <Link href="/feedback" className="fixed bottom-4 right-4 z-20 inline-flex items-center gap-2 rounded-full bg-slate-900 px-4 py-2.5 text-sm font-medium text-white shadow-lg shadow-slate-900/20 transition hover:bg-slate-700 lg:hidden">
          <MessageSquare className="h-4 w-4" />
          Feedback
        </Link>
      )}
    </div>
  );
}
