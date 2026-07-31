import Link from 'next/link';
import { ArrowRight, Clock, History, Sparkles } from 'lucide-react';

const historyItems = [];

export default function HistoryPage() {
  return (
    <section className="mx-auto max-w-6xl px-6 py-10 space-y-8">
      <section className="overflow-hidden rounded-2xl bg-linear-to-br from-slate-900 via-slate-900 to-indigo-950 p-8 text-white shadow-sm">
        <p className="text-sm font-medium text-indigo-200">History</p>
        <h1 className="mt-2 text-3xl font-semibold sm:text-4xl">Your completed jobs will show up here</h1>
        <p className="mt-3 max-w-2xl text-sm text-slate-300 sm:text-base">
          When a user finishes a dubbing job, it will appear here with the final export details and download options.
        </p>

        <div className="mt-6 flex flex-wrap gap-3">
          <Link
            href="/dashboard"
            className="inline-flex items-center gap-2 rounded-lg bg-white px-5 py-2.5 text-sm font-semibold text-slate-900 shadow-sm transition hover:bg-slate-100"
          >
            <History className="h-4 w-4" />
            Go to dashboard
          </Link>
          <Link
            href="/"
            className="inline-flex items-center gap-2 rounded-lg border border-white/20 bg-white/10 px-5 py-2.5 text-sm font-semibold text-white transition hover:bg-white/20"
          >
            <Sparkles className="h-4 w-4" />
            Back to home
          </Link>
        </div>
      </section>

      <div className="rounded-xl border border-indigo-100 bg-white shadow-[0_16px_40px_-24px_rgba(15,23,42,0.28)]">
        <div className="flex flex-col gap-3 border-b border-slate-100 p-5 sm:flex-row sm:items-center sm:justify-between">
          <div>
            <p className="text-sm font-medium text-indigo-600">Recent Jobs</p>
            <h2 className="text-base font-semibold text-slate-900">
              {historyItems.length === 0
                ? 'No completed jobs yet'
                : `${historyItems.length} completed job${historyItems.length !== 1 ? 's' : ''}`}
            </h2>
          </div>

          <div className="inline-flex items-center gap-2 rounded-lg border border-slate-200 bg-slate-50 px-3 py-2 text-sm text-slate-500">
            <Clock className="h-4 w-4" />
            Ready when jobs finish
          </div>

          <button
            type="button"
            disabled={historyItems.length === 0}
            className="inline-flex items-center justify-center rounded-lg border border-red-200 bg-red-50 px-3 py-2 text-sm font-semibold text-red-700 transition hover:bg-red-100 disabled:cursor-not-allowed disabled:opacity-50"
          >
            Clear history
          </button>
        </div>

        <div className="p-8 text-center">
          <p className="text-lg font-semibold text-slate-900">Your job history will show up here</p>
          <p className="mt-2 text-sm text-slate-500">
            As users complete work, the finished jobs can appear in this list with status and download details.
          </p>
          <Link
            href="/dashboard"
            className="mt-5 inline-flex items-center gap-2 rounded-lg bg-slate-900 px-5 py-2.5 text-sm font-semibold text-white shadow-sm transition hover:bg-slate-800"
          >
            Open dashboard
            <ArrowRight className="h-4 w-4" />
          </Link>
        </div>
      </div>
    </section>
  );
}