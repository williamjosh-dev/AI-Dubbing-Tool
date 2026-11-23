'use client';

import { useState } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { ArrowRight, AudioLines, LoaderCircle, Waves } from 'lucide-react';
import { authClient } from '../auth-client';

export default function AuthForm({ mode }) {
  const isSignUp = mode === 'sign-up';
  const router = useRouter();
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState('');

  async function handleSubmit(event) {
    event.preventDefault();
    if (isSubmitting) return;

    const formData = new FormData(event.currentTarget);
    setError('');
    setIsSubmitting(true);

    try {
      const result = isSignUp
        ? await authClient.signUp.email({
            name: String(formData.get('name') || '').trim(),
            email: String(formData.get('email') || '').trim(),
            password: String(formData.get('password') || ''),
          })
        : await authClient.signIn.email({
            email: String(formData.get('email') || '').trim(),
            password: String(formData.get('password') || ''),
          });

      if (result.error) {
        setError(result.error.message || 'We could not complete your request. Please try again.');
        return;
      }

      router.replace('/dashboard');
      router.refresh();
    } catch {
      setError('We could not reach the sign-in service. Check your connection and try again.');
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <main className="min-h-screen bg-[#f7f5f2] text-slate-950 md:grid md:grid-cols-2">
      <section className="relative flex min-h-[120px] flex-col justify-between overflow-hidden bg-[#201634] px-5 py-4 text-white sm:px-10 md:min-h-screen md:px-12 md:py-10 lg:px-16">
        <div className="pointer-events-none absolute -right-28 top-12 h-72 w-72 rounded-full bg-violet-500/20 blur-3xl" />
        <div className="pointer-events-none absolute -bottom-36 -left-16 h-80 w-80 rounded-full bg-cyan-400/10 blur-3xl" />
        <Link href="/" className="relative z-10 inline-flex w-fit items-center gap-2.5" aria-label="Voxa home">
          <span className="flex h-9 w-9 items-center justify-center rounded-xl bg-violet-400 text-[#201634]"><Waves size={19} strokeWidth={2.4} /></span>
          <span className="text-lg font-semibold tracking-tight">voxa<span className="text-violet-300">.</span></span>
        </Link>

        <div className="relative z-10 hidden max-w-lg md:block">
          <div className="mb-7 flex h-14 w-14 items-center justify-center rounded-2xl border border-white/10 bg-white/[0.06] text-violet-200">
            <AudioLines size={26} strokeWidth={1.7} />
          </div>
          <p className="text-sm font-medium text-violet-200">Your voice, everywhere</p>
          <h1 className="mt-3 text-4xl font-medium leading-tight tracking-[-0.04em] lg:text-5xl">
            Make every story sound at home.
          </h1>
          <p className="mt-5 max-w-md text-base leading-7 text-white/65">
            Pick up where inspiration left off. Your dubbing workspace is ready when you are.
          </p>
          <div className="mt-12 flex items-center gap-3 text-sm text-white/55">
            <span className="flex -space-x-2" aria-hidden="true">
              <span className="h-7 w-7 rounded-full border-2 border-[#201634] bg-cyan-200" />
              <span className="h-7 w-7 rounded-full border-2 border-[#201634] bg-violet-300" />
              <span className="h-7 w-7 rounded-full border-2 border-[#201634] bg-amber-200" />
            </span>
            Built for the stories worth sharing
          </div>
        </div>
        <p className="relative z-10 hidden text-xs text-white/40 md:block">A little closer to being understood.</p>
      </section>

      <section className="flex items-center justify-center px-5 py-10 sm:px-8 md:min-h-screen md:px-10 lg:px-16">
        <div className="w-full max-w-md">
          <div className="mb-8 md:mb-10">
            <p className="text-sm font-semibold text-violet-700">{isSignUp ? 'Start creating' : 'Welcome back'}</p>
            <h2 className="mt-2 text-3xl font-semibold tracking-[-0.04em] text-slate-950">
              {isSignUp ? 'Create your account' : 'Log in to Voxa'}
            </h2>
            <p className="mt-2 text-sm leading-6 text-slate-600">
              {isSignUp ? 'Set up your workspace and bring your next voice to life.' : 'Your next dubbing project is just around the corner.'}
            </p>
          </div>

          <form onSubmit={handleSubmit} className="space-y-5" aria-busy={isSubmitting}>
            {isSignUp && (
              <div>
                <label htmlFor="name" className="mb-2 block text-sm font-medium text-slate-800">Full name</label>
                <input id="name" name="name" type="text" autoComplete="name" required maxLength={80} placeholder="Your name" className="auth-input" />
              </div>
            )}
            <div>
              <label htmlFor="email" className="mb-2 block text-sm font-medium text-slate-800">Email address</label>
              <input id="email" name="email" type="email" autoComplete="email" required maxLength={254} placeholder="you@example.com" className="auth-input" />
            </div>
            <div>
              <div className="mb-2 flex items-center justify-between gap-3">
                <label htmlFor="password" className="block text-sm font-medium text-slate-800">Password</label>
                {!isSignUp && <span className="text-xs text-slate-500">Use your account password</span>}
              </div>
              <input id="password" name="password" type="password" autoComplete={isSignUp ? 'new-password' : 'current-password'} required minLength={isSignUp ? 8 : undefined} maxLength={128} placeholder={isSignUp ? 'At least 8 characters' : 'Enter your password'} className="auth-input" />
            </div>

            {error && <p role="alert" className="rounded-xl border border-rose-200 bg-rose-50 px-4 py-3 text-sm leading-5 text-rose-800">{error}</p>}

            <button type="submit" disabled={isSubmitting} className="inline-flex w-full items-center justify-center gap-2 rounded-xl bg-[#201634] px-5 py-3.5 text-sm font-semibold text-white shadow-sm transition hover:bg-violet-900 disabled:cursor-not-allowed disabled:opacity-70">
              {isSubmitting ? <LoaderCircle className="h-4 w-4 animate-spin" aria-hidden="true" /> : null}
              {isSubmitting ? (isSignUp ? 'Creating your account…' : 'Logging you in…') : (isSignUp ? 'Create account' : 'Log in')}
              {!isSubmitting && <ArrowRight className="h-4 w-4" aria-hidden="true" />}
            </button>
          </form>

          <p className="mt-7 text-center text-sm text-slate-600">
            {isSignUp ? 'Already have an account?' : 'New to Voxa?'}{' '}
            <Link href={isSignUp ? '/sign-in' : '/sign-up'} className="font-semibold text-violet-800 underline-offset-4 hover:underline">
              {isSignUp ? 'Log in' : 'Create an account'}
            </Link>
          </p>
          <p className="mt-8 text-center text-xs leading-5 text-slate-500">
            By continuing, you agree to use Voxa responsibly and keep your account details secure.
          </p>
        </div>
      </section>
    </main>
  );
}
