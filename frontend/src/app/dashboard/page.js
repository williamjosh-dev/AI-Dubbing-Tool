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
  },
  {
    title: 'Active Model',
    value: 'Whisper + XTTS',
    detail: 'Transcription, translation & synthesis',
    icon: Cpu,
    trend: 'Stable · v2.3',
  },
  {
    title: 'Export Targets',
    value: 'MP4 · WAV',
    detail: 'Default output for beta testing',
    icon: FileDown,
    trend: '2 formats available',
  },
];

const jobRows = [
  { name: 'episode-12.mp4', status: 'Transcribing', lang: 'ES → EN', progress: 35 },
  { name: 'tutorial-audio.wav', status: 'Translating', lang: 'FR → EN', progress: 62 },
  { name: 'product-demo.mov', status: 'Rendering', lang: 'DE → EN', progress: 88 },
];

const statusStyles = {
  Transcribing: 'bg-amber-50 text-amber-700 ring-amber-600/20',
  Translating: 'bg-blue-50 text-blue-700 ring-blue-600/20',
  Rendering: 'bg-violet-50 text-violet-700 ring-violet-600/20',
};

export default function DashboardPage() {
  const [query, setQuery] = useState('');
  const filteredJobs = jobRows.filter((job) =>
    job.name.toLowerCase().includes(query.toLowerCase())
  );

  return (
    <section className="mx-auto max-w-6xl px-6 py-10 space-y-8">
      <div className="flex flex-col gap-4 sm:flex-row sm:items-end sm:justify-between">
        <div>
          <p className="text-sm font-medium text-indigo-600">Dashboard</p>
          <h1 className="mt-1 text-2xl font-semibold text-slate-900">
            Operational control for dubbing jobs
          </h1>
          <p className="mt-1 text-sm text-slate-500">
            Track pipeline progress, review job state, and keep the beta workflow organized.
          </p>
        </div>
        <Link
          href="/"
          className="inline-flex items-center justify-center rounded-lg bg-slate-900 px-4 py-2.5 text-sm font-medium text-white shadow-sm transition hover:bg-slate-800"
        >
          <Upload className="mr-2 h-4 w-4" />
          New Upload
        </Link>
      </div>

      <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
        {pipelineCards.map(({ title, value, detail, icon: Icon, trend }) => (
          <article
            key={title}
            className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm transition hover:shadow-md"
          >
            <div className="flex items-center justify-between">
              <p className="text-sm font-medium text-slate-500">{title}</p>
              <div className="rounded-lg bg-indigo-50 p-2">
                <Icon className="h-4 w-4 text-indigo-600" />
              </div>
            </div>
            <p className="mt-3 text-xl font-semibold text-slate-900">{value}</p>
            <p className="mt-1 text-sm text-slate-500">{detail}</p>
            <p className="mt-3 text-xs font-medium text-emerald-600">{trend}</p>
          </article>
        ))}
      </div>

      <div className="rounded-xl border border-slate-200 bg-white shadow-sm">
        <div className="flex flex-col gap-3 border-b border-slate-100 p-5 sm:flex-row sm:items-center sm:justify-between">
          <div>
            <p className="text-sm font-medium text-indigo-600">Live Jobs</p>
            <h2 className="text-base font-semibold text-slate-900">
              {filteredJobs.length} job{filteredJobs.length !== 1 ? 's' : ''} in progress
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
          {filteredJobs.length === 0 && (
            <p className="p-6 text-center text-sm text-slate-400">No jobs match your search.</p>
          )}
          {filteredJobs.map((job) => (
            <div key={job.name} className="flex items-center justify-between gap-4 px-5 py-4">
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