import './global.css';
import AppShell from './components/app-shell';

export const metadata = {
  title: 'Voxa — Voice dubbing studio',
  description: 'Create natural-sounding dubs for your audio and video. Translate your story, synthesize a voice, and share it with the world.',
  applicationName: 'Voxa',
};

export const viewport = {
  themeColor: '#f7f5f2',
};

export default function RootLayout({ children }) {
  return (
    <html lang="en" suppressHydrationWarning>
      <body className="bg-slate-50 text-slate-900 antialiased" suppressHydrationWarning>
        <AppShell>{children}</AppShell>
      </body>
    </html>
  );
}
