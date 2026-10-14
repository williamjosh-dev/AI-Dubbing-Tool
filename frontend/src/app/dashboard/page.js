'use client';

import { useState } from 'react';
import Link from 'next/link';
import { Upload, Clock, Cpu, FileDown, Search, MoreVertical } from 'lucide-react';

const pipelineCards = [
  {
    title: 'Queued Uploads',
    value: '3',
    detail: 'Files waiting to enter the pipeline',
    icon: Upload,
    trend: '+1 in the last 10 min',
    accent: 'indigo',
  },
  {
    title: 'Active Model',
    value: 'Whisper + XTTS',
    detail: 'Transcription, translation & synthesis',
    icon: Cpu,
    trend: 'Stable · v2.3',
    accent: 'emerald',
  },
  {
    title: 'Export Targets',
    value: 'MP4 · WAV',
    detail: 'Default output for beta testing',
    icon: FileDown,
    trend: '2 formats available',
    accent: 'amber',
  },
];

const cardAccentStyles = {
  indigo: {
    border: 'border-indigo-100',
    iconBg: 'bg-indigo-50',
    iconText: 'text-indigo-600',
    trend: 'text-indigo-600',
  },
  emerald: {
    border: 'border-emerald-100',
    iconBg: 'bg-emerald-50',
    iconText: 'text-emerald-600',
    trend: 'text-emerald-600',
  },
  amber: {
    border: 'border-amber-100',
    iconBg: 'bg-amber-50',
    iconText: 'text-amber-600',
    trend: 'text-amber-600',
  },
};

const statusStyles = {
  Queued: 'bg-slate-100 text-slate-700 ring-slate-600/20',
  Transcribing: 'bg-amber-50 text-amber-700 ring-amber-600/20',
  Translating: 'bg-blue-50 text-blue-700 ring-blue-600/20',
  Rendering: 'bg-violet-50 text-violet-700 ring-violet-600/20',
};

export default function DashboardPage() {
  const [query, setQuery] = useState('');
  const [jobs, setJobs] = useState([]);

  const filteredJobs = jobs.filter((job) =>
    job.name.toLowerCase().includes(query.toLowerCase())
  );

  const handleNewUpload = () => {
    const newJob = {
      id: Date.now(),
      name: `New upload ${jobs.length + 1}`,
      status: 'Queued',
      lang: 'EN → ES',
      progress: 8,
    };

    setJobs((currentJobs) => [newJob, ...currentJobs]);
  };

  return (
    <section className="mx-auto max-w-6xl px-6 py-10 space-y-8">
      <section className="overflow-hidden rounded-2xl bg-gradient-to-br from-slate-900 via-slate-900 to-indigo-950 p-8 text-white shadow-sm">
        <p className="text-sm font-medium text-indigo-200">Dashboard</p>
        <h1 className="mt-2 text-3xl font-semibold sm:text-4xl">Keep your dubbing jobs organized</h1>
        <p className="mt-3 max-w-2xl text-sm text-slate-300 sm:text-base">
          Track progress, review job status, and stay on top of each upload from one place.
        </p>

        <div className="mt-6 flex flex-wrap gap-3">
          <button
            type="button"
            onClick={handleNewUpload}
            className="inline-flex items-center gap-2 rounded-lg bg-white px-5 py-2.5 text-sm font-semibold text-slate-900 shadow-sm transition hover:bg-slate-100"
          >
            <Upload className="h-4 w-4" />
            New Upload
          </button>
          <Link
            href="/history"
            className="inline-flex items-center gap-2 rounded-lg border border-white/20 bg-white/10 px-5 py-2.5 text-sm font-semibold text-white transition hover:bg-white/20"
          >
            View recent jobs
            <Clock className="h-4 w-4" />
          </Link>
        </div>
      </section>

      <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
        {pipelineCards.map(({ title, value, detail, icon: Icon, trend, accent }) => {
          const styles = cardAccentStyles[accent];

          return (
            <article
              key={title}
              className={`rounded-xl border bg-white p-5 shadow-sm transition hover:shadow-md ${styles.border}`}
            >
              <div className="flex items-center justify-between">
                <p className="text-sm font-medium text-slate-500">{title}</p>
                <div className={`rounded-lg p-2 ${styles.iconBg}`}>
                  <Icon className={`h-4 w-4 ${styles.iconText}`} />
                </div>
              </div>
              <p className="mt-3 text-xl font-semibold text-slate-900">{value}</p>
              <p className="mt-1 text-sm text-slate-500">{detail}</p>
              <p className={`mt-3 text-xs font-medium ${styles.trend}`}>{trend}</p>
            </article>
          );
        })}
      </div>

      <div className="rounded-xl border border-indigo-100 bg-white shadow-[0_16px_40px_-24px_rgba(15,23,42,0.28)]">
        <div className="flex flex-col gap-3 border-b border-slate-100 p-5 sm:flex-row sm:items-center sm:justify-between">
          <div>
            <p className="text-sm font-medium text-indigo-600">Your Jobs</p>
            <h2 className="text-base font-semibold text-slate-900">
              {jobs.length === 0
                ? 'No jobs yet'
                : `${filteredJobs.length} job${filteredJobs.length !== 1 ? 's' : ''} in progress`}
            </h2>
          </div>
          <div className="relative">
            <Search className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-400" />
            <input
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder="Search jobs..."
              className="w-full rounded-lg border border-slate-200 py-2 pl-9 pr-3 text-sm text-slate-700 placeholder:text-slate-400 focus:border-indigo-400 focus:outline-none focus:ring-2 focus:ring-indigo-100 sm:w-56"
            />
          </div>
        </div>

        <div className="divide-y divide-slate-100">
          {jobs.length === 0 && (
            <div className="p-8 text-center">
              <p className="text-lg font-semibold text-slate-900">Your jobs will show up here</p>
              <p className="mt-2 text-sm text-slate-500">
                Once a user uploads a new job, it will appear in this list automatically.
              </p>
            </div>
          )}

          {jobs.length > 0 && filteredJobs.length === 0 && (
            <div className="p-8 text-center">
              <p className="text-lg font-semibold text-slate-900">No jobs match your search</p>
              <p className="mt-2 text-sm text-slate-500">Try a different keyword to find the job you need.</p>
            </div>
          )}

          {filteredJobs.map((job) => (
            <div key={job.id} className="flex items-center justify-between gap-4 px-5 py-4">
              <div className="min-w-0 flex-1">
                <div className="flex items-center gap-2">
                  <strong className="truncate text-sm font-medium text-slate-900">{job.name}</strong>
                  <span className="text-xs text-slate-400">{job.lang}</span>
                </div>
                <div className="mt-2 h-1.5 w-full max-w-xs overflow-hidden rounded-full bg-slate-100">
                  <div
                    className="h-full rounded-full bg-indigo-500 transition-all"
                    style={{ width: `${job.progress}%` }}
                  />
                </div>
              </div>

              <span
                className={`inline-flex items-center gap-1 whitespace-nowrap rounded-full px-2.5 py-1 text-xs font-medium ring-1 ring-inset ${statusStyles[job.status]}`}
              >
                <Clock className="h-3 w-3" />
                {job.status}
              </span>

              <button className="rounded-md p-1.5 text-slate-400 hover:bg-slate-50 hover:text-slate-600">
                <MoreVertical className="h-4 w-4" />
              </button>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}