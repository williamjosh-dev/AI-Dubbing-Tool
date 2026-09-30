'use client';

import Link from 'next/link';
import { useState } from 'react';
import { ArrowLeft, CheckCircle2, MessageSquare, Send } from 'lucide-react';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL || '';

const categories = [
    { value: 'general', label: 'General feedback' },
    { value: 'feature', label: 'Feature request' },
    { value: 'bug', label: 'Report a problem' },
];

const ratings = [1, 2, 3, 4, 5];

function formatError(error) {
    if (!error) return 'Something went wrong while sending your feedback.';
    if (typeof error === 'string') return error;
    return error.detail || error.message || 'Something went wrong while sending your feedback.';
}

export default function FeedbackPage() {
    const [category, setCategory] = useState('general');
    const [rating, setRating] = useState(5);
    const [message, setMessage] = useState('');
    const [email, setEmail] = useState('');
    const [isSubmitting, setIsSubmitting] = useState(false);
    const [error, setError] = useState('');
    const [isSubmitted, setIsSubmitted] = useState(false);

    const handleSubmit = async (event) => {
        event.preventDefault();
        setIsSubmitting(true);
        setError('');

        try {
            const response = await fetch(`${API_BASE_URL}/api/feedback`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    category,
                    rating,
                    message,
                    email: email || null,
                    page: window.location.pathname,
                }),
            });
            const data = await response.json();

            if (!response.ok) {
                throw new Error(formatError(data));
            }

            setIsSubmitted(true);
        } catch (submitError) {
            setError(submitError instanceof Error ? submitError.message : formatError(submitError));
        } finally {
            setIsSubmitting(false);
        }
    };

    if (isSubmitted) {
        return (
            <section className="page-shell">
                <div className="mx-auto max-w-2xl">
                    <div className="panel text-center">
                        <div className="mx-auto flex h-14 w-14 items-center justify-center rounded-full bg-emerald-50 text-emerald-600">
                            <CheckCircle2 className="h-7 w-7" />
                        </div>
                        <h1 className="mt-5 text-2xl font-semibold text-slate-900">Thanks for the feedback</h1>
                        <p className="mx-auto mt-3 max-w-md text-sm leading-6 text-slate-600">
                            Your note will help us improve the dubbing experience for the beta.
                        </p>
                        <div className="mt-6 flex flex-wrap justify-center gap-3">
                            <Link href="/dubbing" className="btn-primary">
                                Back to dubbing
                            </Link>
                            <Link href="/" className="btn-secondary">
                                Go home
                            </Link>
                        </div>
                    </div>
                </div>
            </section>
        );
    }

    return (
        <section className="page-shell">
            <div className="mx-auto max-w-2xl">
                <Link href="/" className="inline-flex items-center gap-2 text-sm font-medium text-slate-500 transition hover:text-slate-900">
                    <ArrowLeft className="h-4 w-4" />
                    Back home
                </Link>

                <div className="mt-5 overflow-hidden rounded-2xl bg-gradient-to-br from-slate-900 via-slate-900 to-indigo-950 p-7 text-white shadow-sm sm:p-8">
                    <div className="flex h-11 w-11 items-center justify-center rounded-xl bg-white/10 text-indigo-200">
                        <MessageSquare className="h-5 w-5" />
                    </div>
                    <p className="mt-5 text-sm font-medium text-indigo-200">Beta feedback</p>
                    <h1 className="mt-2 text-3xl font-semibold">Help shape the dubbing studio</h1>
                    <p className="mt-3 max-w-xl text-sm leading-6 text-slate-300">
                        Tell us what worked, what felt unclear, or what would make your next project easier.
                    </p>
                </div>

                <form onSubmit={handleSubmit} className="panel mt-6 space-y-6">
                    <div>
                        <label htmlFor="feedback-category" className="text-sm font-semibold text-slate-900">
                            What kind of feedback is this?
                        </label>
                        <select
                            id="feedback-category"
                            value={category}
                            onChange={(event) => setCategory(event.target.value)}
                            className="mt-2 w-full rounded-lg border border-slate-300 bg-white px-3 py-2.5 text-sm text-slate-700 focus:border-indigo-500 focus:outline-none focus:ring-2 focus:ring-indigo-100"
                        >
                            {categories.map((option) => (
                                <option key={option.value} value={option.value}>{option.label}</option>
                            ))}
                        </select>
                    </div>

                    <fieldset>
                        <legend className="text-sm font-semibold text-slate-900">How was your experience?</legend>
                        <div className="mt-3 grid grid-cols-5 gap-2" role="radiogroup" aria-label="Feedback rating">
                            {ratings.map((value) => (
                                <button
                                    key={value}
                                    type="button"
                                    role="radio"
                                    aria-checked={rating === value}
                                    onClick={() => setRating(value)}
                                    className={`min-h-11 rounded-lg border text-sm font-semibold transition ${rating === value
                                        ? 'border-indigo-600 bg-indigo-600 text-white shadow-sm'
                                        : 'border-slate-200 bg-slate-50 text-slate-600 hover:border-indigo-300 hover:bg-indigo-50 hover:text-indigo-700'
                                        }`}
                                >
                                    {value}
                                </button>
                            ))}
                        </div>
                        <div className="mt-2 flex justify-between text-xs text-slate-400">
                            <span>Needs work</span>
                            <span>Excellent</span>
                        </div>
                    </fieldset>

                    <div>
                        <label htmlFor="feedback-message" className="text-sm font-semibold text-slate-900">
                            What should we know?
                        </label>
                        <textarea
                            id="feedback-message"
                            value={message}
                            onChange={(event) => setMessage(event.target.value)}
                            required
                            maxLength={2000}
                            rows={6}
                            placeholder="Share a specific moment, idea, or problem..."
                            className="mt-2 w-full resize-y rounded-lg border border-slate-300 px-3 py-2.5 text-sm text-slate-700 placeholder:text-slate-400 focus:border-indigo-500 focus:outline-none focus:ring-2 focus:ring-indigo-100"
                        />
                        <p className="mt-1 text-right text-xs text-slate-400">{message.length}/2000</p>
                    </div>

                    <div>
                        <label htmlFor="feedback-email" className="text-sm font-semibold text-slate-900">
                            Email <span className="font-normal text-slate-400">(optional)</span>
                        </label>
                        <input
                            id="feedback-email"
                            type="email"
                            value={email}
                            onChange={(event) => setEmail(event.target.value)}
                            placeholder="you@example.com"
                            className="mt-2 w-full rounded-lg border border-slate-300 px-3 py-2.5 text-sm text-slate-700 placeholder:text-slate-400 focus:border-indigo-500 focus:outline-none focus:ring-2 focus:ring-indigo-100"
                        />
                        <p className="mt-1 text-xs text-slate-400">Only add this if you would like a reply.</p>
                    </div>

                    {error && (
                        <div role="alert" className="rounded-xl border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-800">
                            {error}
                        </div>
                    )}

                    <div className="flex flex-wrap items-center justify-between gap-3 border-t border-slate-100 pt-5">
                        <p className="text-xs text-slate-400">Your feedback is stored securely for beta review.</p>
                        <button type="submit" disabled={isSubmitting} className="btn-primary disabled:cursor-not-allowed disabled:opacity-60">
                            <Send className="h-4 w-4" />
                            {isSubmitting ? 'Sending...' : 'Send feedback'}
                        </button>
                    </div>
                </form>
            </div>
        </section>
    );
}
