import Link from 'next/link';
import { ArrowRight, Clock3, ListChecks, Sparkles, UploadCloud } from 'lucide-react';

const stats = [
  { label: 'Queued Jobs', value: '08', hint: '+2 in the last hour', icon: ListChecks },
  { label: 'Processed Minutes', value: '124', hint: 'Today across all jobs', icon: Clock3 },
  { label: 'Supported Formats', value: '6', hint: 'Video and audio inputs', icon: Sparkles },
];

const steps = [
  { title: 'Upload a media file', detail: 'Drop in video or audio — MP4, MOV, WAV and more.' },
  { title: 'Pick source and target languages', detail: 'Choose from 30+ language pairs.' },
  { title: 'Run transcription, translation & TTS', detail: 'Our pipeline handles it end-to-end.' },
  { title: 'Review the output in history', detail: 'Download or share once it’s ready.' },
];

export default function HomePage() {
  return (
    <div className="mx-auto max-w-6xl px-6 py-12 space-y-12">
      <section className="overflow-hidden rounded-2xl bg-linear-to-br from-slate-900 to-slate-800 p-10 text-white shadow-lg">
        <p className="inline-flex items-center gap-1.5 rounded-full bg-white/10 px-3 py-1 text-xs font-medium text-indigo-200">
          <Sparkles className="h-3.5 w-3.5" />
          AI Dubbing, reimagined
        </p>
        <h1 className="mt-4 max-w-xl text-3xl font-semibold leading-tight sm:text-4xl">
          Ship dubbing jobs from one place.
        </h1>
        <p className="mt-3 max-w-lg text-sm text-slate-300 sm:text-base">
          Upload, translate, and export multilingual video in minutes. Your entry point for
          uploads, job status, and upcoming beta workflows.
        </p>
        <div className="mt-6 flex flex-wrap gap-3">
          <Link
            href="/dashboard"
            className="inline-flex items-center gap-2 rounded-lg bg-white px-5 py-2.5 text-sm font-medium text-slate-900 shadow-sm transition hover:bg-slate-100"
          >
            <UploadCloud className="h-4 w-4" />
            Open Dashboard
          </Link>
          <Link
            href="/history"
            className="inline-flex items-center gap-2 rounded-lg border border-white/20 px-5 py-2.5 text-sm font-medium text-white transition hover:bg-white/10"
          >
            View History
            <ArrowRight className="h-4 w-4" />
          </Link>
        </div>
      </section>

      <section className="grid grid-cols-1 gap-4 sm:grid-cols-3">
        {stats.map(({ label, value, hint, icon: Icon }) => (
          <article
            key={label}
            className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm transition hover:shadow-md"
          >
            <div className="flex items-center justify-between">
              <p className="text-sm font-medium text-slate-500">{label}</p>
              <div className="rounded-lg bg-indigo-50 p-2">
                <Icon className="h-4 w-4 text-indigo-600" />
              </div>
            </div>
            <p className="mt-3 text-2xl font-semibold text-slate-900">{value}</p>
            <p className="mt-1 text-sm text-slate-500">{hint}</p>
          </article>
        ))}
      </section>

      <section className="rounded-xl border border-slate-200 bg-white p-6 shadow-sm">
        <p className="text-sm font-medium text-indigo-600">Workflow</p>
        <h2 className="mt-1 text-lg font-semibold text-slate-900">What the app does on every job</h2>
        <ol className="mt-5 grid grid-cols-1 gap-5 sm:grid-cols-2">
          {steps.map((step, i) => (
            <li key={step.title} className="flex gap-3">
              <span className="flex h-7 w-7 shrink-0 items-center justify-center rounded-full bg-indigo-600 text-xs font-semibold text-white">
                {i + 1}
              </span>
              <div>
                <p className="text-sm font-medium text-slate-900">{step.title}</p>
                <p className="text-sm text-slate-500">{step.detail}</p>
              </div>
            </li>
          ))}
        </ol>
      </section>

      <section className="flex flex-col items-start justify-between gap-5 rounded-xl border border-slate-200 bg-slate-50 p-6 sm:flex-row sm:items-center">
        <div>
          <p className="text-sm font-medium text-indigo-600">Quick Actions</p>
          <h2 className="mt-1 text-lg font-semibold text-slate-900">
            Routes are ready for a dashboard-first flow.
          </h2>
          <p className="mt-1 max-w-md text-sm text-slate-500">
            Keep uploads on the home route, use dashboard for operational status, and reserve
            history for completed jobs.
          </p>
        </div>
        <div className="flex shrink-0 gap-3">
          <Link
            href="/dashboard"
            className="rounded-lg border border-slate-300 bg-white px-4 py-2 text-sm font-medium text-slate-700 transition hover:bg-slate-50"
          >
            Go to dashboard
          </Link>
          <Link
            href="/history"
            className="rounded-lg border border-slate-300 bg-white px-4 py-2 text-sm font-medium text-slate-700 transition hover:bg-slate-50"
          >
            Open history
          </Link>
        </div>
      </section>
    </div>
  );
}