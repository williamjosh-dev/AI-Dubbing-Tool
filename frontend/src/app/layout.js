import './global.css';
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
        </div>
      </body>
    </html>
  );
}
