import Link from 'next/link';
import { ArrowRight, PlayCircle, Sparkles, UploadCloud } from 'lucide-react';

const steps = [
  { title: 'Upload a file', detail: 'Start with a video or audio clip that needs dubbing.' },
  { title: 'Choose languages', detail: 'Pick the source and target languages for the project.' },
  { title: 'Review the result', detail: 'Check the generated output and move it to the next job.' },
];

const highlights = [
  { title: 'Fast to start', detail: 'A simple flow helps new users begin without confusion.' },
  { title: 'Easy to follow', detail: 'Each step is clear and keeps the process organized.' },
  { title: 'Built for progress', detail: 'Dashboard and history make it easy to track work.' },
];

export default function HomePage() {
  return (
    <main className="mx-auto max-w-6xl px-6 py-10 space-y-8">
      <section className="overflow-hidden rounded-2xl bg-gradient-to-br from-slate-900 via-slate-900 to-indigo-950 p-8 text-white shadow-sm">
        <p className="text-sm font-medium text-indigo-200">Welcome</p>
        <h1 className="mt-2 text-3xl font-semibold sm:text-4xl">Create your first dubbing project</h1>
        <p className="mt-3 max-w-2xl text-sm text-slate-300 sm:text-base">
          Upload a file, pick your languages, and move through the workflow with a clear and simple experience.
        </p>

        <div className="mt-6 flex flex-wrap gap-3">
          <Link
            href="/dashboard"
            className="inline-flex items-center gap-2 rounded-lg bg-white px-5 py-2.5 text-sm font-semibold text-slate-900 shadow-sm transition hover:bg-slate-100"
          >
            <UploadCloud className="h-4 w-4" />
            Get Started
          </Link>
          <Link
            href="/history"
            className="inline-flex items-center gap-2 rounded-lg border border-white/20 bg-white/10 px-5 py-2.5 text-sm font-semibold text-white transition hover:bg-white/20"
          >
            View recent jobs
            <ArrowRight className="h-4 w-4" />
          </Link>
        </div>
      </section>

      <section className="grid gap-4 lg:grid-cols-[1.2fr_0.8fr]">
        <div className="rounded-xl border border-indigo-100 bg-indigo-50/70 p-6 shadow-sm">
          <div className="flex items-center gap-2">
            <PlayCircle className="h-5 w-5 text-indigo-600" />
            <h2 className="text-lg font-semibold text-slate-900">How the workflow works</h2>
          </div>

          <div className="mt-4 space-y-3">
            {steps.map((step, index) => (
              <div key={step.title} className="rounded-lg border border-slate-200 bg-slate-50 p-4">
                <div className="flex items-start gap-3">
                  <span className="flex h-7 w-7 shrink-0 items-center justify-center rounded-full bg-indigo-600 text-sm font-semibold text-white">
                    {index + 1}
                  </span>
                  <div>
                    <p className="text-sm font-semibold text-slate-900">{step.title}</p>
                    <p className="mt-1 text-sm text-slate-600">{step.detail}</p>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>

        <div className="rounded-xl border border-slate-200 bg-slate-100/80 p-6 shadow-sm">
          <div className="flex items-center gap-2">
            <Sparkles className="h-5 w-5 text-indigo-600" />
            <h2 className="text-lg font-semibold text-slate-900">Starter friendly</h2>
          </div>
          <p className="mt-3 text-sm text-slate-600">
            This page is designed to feel clear and welcoming for first-time users while staying easy to build on.
          </p>

          <div className="mt-4 rounded-lg border border-slate-200 bg-white/80 p-4">
            <p className="text-sm font-semibold text-slate-900">Quick tip</p>
            <p className="mt-1 text-sm text-slate-600">
              Start with a short sample file to test the full experience before using a larger project.
            </p>
          </div>
        </div>
      </section>

      <section className="grid gap-4 md:grid-cols-3">
        {highlights.map((item) => (
          <div key={item.title} className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm">
            <h3 className="text-sm font-semibold text-slate-900">{item.title}</h3>
            <p className="mt-2 text-sm text-slate-600">{item.detail}</p>
          </div>
        ))}
      </section>
    </main>
  );
}