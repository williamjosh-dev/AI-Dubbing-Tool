import Link from 'next/link';
import {
  ArrowDownRight,
  ArrowRight,
  AudioLines,
  Check,
  Clapperboard,
  Globe2,
  Headphones,
  Languages,
  Mic2,
  Play,
  Sparkles,
  Upload,
  Waves,
} from 'lucide-react';

const workflow = [
  { number: '01', icon: Upload, title: 'Add your media', detail: 'Bring in a video or audio file. Your original stays untouched.' },
  { number: '02', icon: Languages, title: 'Choose your languages', detail: 'Set the source and destination languages for your audience.' },
  { number: '03', icon: AudioLines, title: 'Create your dub', detail: 'Transcription, translation, and voice synthesis work together.' },
  { number: '04', icon: Headphones, title: 'Review and export', detail: 'Listen through your result and download the finished files.' },
];

const voices = [
  { label: 'Original', color: 'bg-cyan-300', bars: [18, 33, 25, 44, 30, 57, 36, 49, 24, 41, 31, 55, 26, 39, 19, 33, 47, 29, 42, 21] },
  { label: 'Español', color: 'bg-violet-400', bars: [29, 19, 43, 27, 50, 34, 22, 46, 30, 55, 20, 39, 28, 47, 24, 36, 53, 23, 40, 31] },
];

export default function HomePage() {
  return (
    <main className="min-h-screen overflow-hidden bg-[var(--background)] text-[var(--foreground)]">
      <header className="mx-auto flex max-w-7xl items-center justify-between px-5 py-5 sm:px-8 lg:px-12">
        <Link href="/" className="flex items-center gap-2.5" aria-label="Voxa home">
          <span className="flex h-9 w-9 items-center justify-center rounded-xl bg-[var(--accent)] text-white"><Waves size={19} strokeWidth={2.4} /></span>
          <span className="text-lg font-semibold tracking-tight">voxa<span className="text-[var(--accent)]">.</span></span>
        </Link>
        <nav className="hidden items-center gap-8 text-sm text-[var(--muted-foreground)] md:flex" aria-label="Main navigation">
          <a href="#workflow" className="transition hover:text-[var(--foreground)]">How it works</a>
          <a href="#features" className="transition hover:text-[var(--foreground)]">Why Voxa</a>
        </nav>
        <div className="flex items-center gap-2 sm:gap-3">
          <Link href="/sign-in" className="rounded-full px-3 py-2 text-sm font-medium text-[var(--foreground)] transition hover:bg-black/5 sm:px-4">Log in</Link>
          <Link href="/sign-up" className="inline-flex items-center gap-2 rounded-full bg-[var(--foreground)] px-4 py-2.5 text-sm font-medium text-white transition hover:bg-[var(--accent)] sm:px-5">Get started <ArrowRight size={15} /></Link>
        </div>
      </header>

      <section className="mx-auto grid max-w-7xl items-center gap-12 px-5 pb-20 pt-12 sm:px-8 sm:pt-16 lg:grid-cols-[1fr_0.92fr] lg:gap-16 lg:px-12 lg:pb-28 lg:pt-20">
        <div className="relative z-10">
          <div className="mb-7 inline-flex items-center gap-2 rounded-full border border-[var(--border)] bg-white/70 px-3.5 py-2 text-xs font-medium text-[var(--muted-foreground)] shadow-sm">
            <Sparkles size={14} className="text-[var(--accent)]" /> Your voice, everywhere
          </div>
          <h1 className="max-w-2xl text-[clamp(3.2rem,7vw,6.2rem)] font-semibold leading-[0.98] tracking-[-0.065em]">Make every voice <span className="font-serif font-normal italic text-[var(--accent)]">global.</span></h1>
          <p className="mt-7 max-w-lg text-base leading-7 text-[var(--muted-foreground)] sm:text-lg sm:leading-8">Turn your audio and video into natural-sounding dubs. Reach new audiences without losing the voice behind your story.</p>
          <div className="mt-8 flex flex-wrap items-center gap-4">
            <Link href="/sign-up" className="inline-flex items-center gap-2.5 rounded-full bg-[var(--accent)] px-6 py-3.5 text-sm font-semibold text-white shadow-lg shadow-violet-500/20 transition hover:-translate-y-0.5 hover:bg-violet-700">Start dubbing <ArrowRight size={16} /></Link>
            <a href="#workflow" className="inline-flex items-center gap-2 rounded-full px-4 py-3 text-sm font-medium text-[var(--foreground)] transition hover:bg-white">See how it works <ArrowDownRight size={15} /></a>
          </div>
          <div className="mt-11 flex items-center gap-3 text-xs text-[var(--muted-foreground)]"><div className="flex -space-x-2"><span className="h-7 w-7 rounded-full border-2 border-[var(--background)] bg-amber-200"/><span className="h-7 w-7 rounded-full border-2 border-[var(--background)] bg-cyan-200"/><span className="h-7 w-7 rounded-full border-2 border-[var(--background)] bg-violet-200"/></div><span>Made for the stories worth sharing</span></div>
        </div>

        <div className="relative mx-auto w-full max-w-xl lg:ml-auto">
          <div className="absolute -right-8 -top-12 h-52 w-52 rounded-full bg-violet-300/30 blur-3xl" />
          <div className="absolute -bottom-12 -left-8 h-48 w-48 rounded-full bg-cyan-200/40 blur-3xl" />
          <div className="relative rounded-[2rem] border border-white/80 bg-white/75 p-4 shadow-[0_30px_90px_-30px_rgba(71,57,125,0.24)] backdrop-blur-xl sm:p-6">
            <div className="flex items-center justify-between border-b border-[var(--border)] pb-4">
              <div className="flex items-center gap-3"><span className="flex h-10 w-10 items-center justify-center rounded-xl bg-violet-50 text-[var(--accent)]"><Clapperboard size={19} /></span><div><p className="text-sm font-semibold">The Sunday Market</p><p className="mt-0.5 text-xs text-[var(--muted-foreground)]">Project preview · 02:14</p></div></div>
              <span className="rounded-full bg-emerald-50 px-2.5 py-1 text-[10px] font-semibold text-emerald-700"><Check size={11} className="mr-1 inline"/>Ready</span>
            </div>
            <div className="my-5 flex aspect-[1.72] items-center justify-center overflow-hidden rounded-2xl bg-[radial-gradient(ellipse_at_50%_100%,rgba(196,181,253,0.55),transparent_55%),linear-gradient(135deg,#f3f0fb,#e8f5f5_55%,#f8eee6)]">
              <div className="relative flex h-28 w-28 items-center justify-center rounded-full border border-white/70 bg-white/40 shadow-inner backdrop-blur-sm sm:h-36 sm:w-36"><div className="absolute inset-4 rounded-full border border-white/80"/><div className="absolute inset-8 rounded-full border border-white/80"/><span className="relative flex h-12 w-12 items-center justify-center rounded-full bg-white text-[var(--accent)] shadow-md"><Play size={18} fill="currentColor" className="ml-0.5" /></span></div>
              <div className="absolute sr-only">Audio dubbing project preview</div>
              <span className="absolute bottom-4 left-5 rounded-full border border-white/70 bg-white/60 px-3 py-1.5 text-[10px] font-medium text-slate-600 backdrop-blur">Original video</span>
              <span className="absolute bottom-4 right-5 flex items-center gap-1.5 rounded-full border border-white/70 bg-white/60 px-3 py-1.5 text-[10px] font-medium text-slate-600 backdrop-blur"><Globe2 size={12}/> English → Español</span>
            </div>
            <div className="space-y-3.5">
              {voices.map((voice) => <div key={voice.label} className="grid grid-cols-[62px_1fr] items-center gap-3"><span className="text-[11px] font-medium text-[var(--muted-foreground)]">{voice.label}</span><div className="flex h-8 items-center justify-between gap-[3px]" aria-label={`${voice.label} audio waveform`}>{voice.bars.map((height, index) => <span key={`${voice.label}-${index}`} className={`w-full max-w-[5px] rounded-full ${voice.color} opacity-80`} style={{height: `${height}%`}} />)}</div></div>)}
            </div>
            <div className="mt-5 flex items-center justify-between border-t border-[var(--border)] pt-4"><span className="flex items-center gap-2 text-xs text-[var(--muted-foreground)]"><Mic2 size={14} className="text-[var(--accent)]"/> Voice matched</span><span className="text-xs font-medium text-[var(--foreground)]">Export ready <ArrowRight size={13} className="ml-1 inline"/></span></div>
          </div>
          <div className="absolute -bottom-6 -left-5 hidden items-center gap-3 rounded-2xl border border-white/80 bg-white/90 px-4 py-3 shadow-xl shadow-slate-900/5 sm:flex"><span className="flex h-9 w-9 items-center justify-center rounded-xl bg-cyan-50 text-cyan-700"><Globe2 size={17}/></span><div><p className="text-xs font-semibold">One story</p><p className="text-[10px] text-[var(--muted-foreground)]">More ways to hear it</p></div></div>
        </div>
      </section>

      <section id="workflow" className="border-y border-[var(--border)] bg-white/55">
        <div className="mx-auto max-w-7xl px-5 py-20 sm:px-8 lg:px-12 lg:py-24">
          <div className="mb-12 flex flex-col justify-between gap-5 md:flex-row md:items-end"><div><p className="mb-3 text-xs font-semibold uppercase tracking-[0.18em] text-[var(--accent)]">A simpler way to dub</p><h2 className="max-w-xl text-3xl font-semibold tracking-[-0.045em] sm:text-4xl">From original to <span className="font-serif font-normal italic">over there.</span></h2></div><p className="max-w-sm text-sm leading-6 text-[var(--muted-foreground)]">A clear, guided workflow takes your media from upload to a ready-to-share localized version.</p></div>
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
            {workflow.map(({number, icon: Icon, title, detail}) => <article key={number} className="group rounded-2xl border border-[var(--border)] bg-[var(--background)] p-5 transition hover:-translate-y-1 hover:border-violet-200 hover:shadow-lg hover:shadow-violet-900/5 sm:p-6"><div className="mb-9 flex items-center justify-between"><span className="text-xs font-medium text-slate-400">{number}</span><span className="flex h-10 w-10 items-center justify-center rounded-xl bg-white text-[var(--accent)] shadow-sm transition group-hover:bg-[var(--accent)] group-hover:text-white"><Icon size={18}/></span></div><h3 className="text-base font-semibold tracking-tight">{title}</h3><p className="mt-2 text-sm leading-6 text-[var(--muted-foreground)]">{detail}</p></article>)}
          </div>
        </div>
      </section>

      <section id="features" className="mx-auto flex max-w-7xl flex-col items-start justify-between gap-8 px-5 py-16 sm:px-8 md:flex-row md:items-center lg:px-12 lg:py-20">
        <div><div className="mb-3 flex items-center gap-2 text-xs font-semibold uppercase tracking-[0.18em] text-[var(--accent)]"><AudioLines size={14}/> Built around your workflow</div><h2 className="max-w-xl text-3xl font-semibold tracking-[-0.045em] sm:text-4xl">Everything in one focused studio.</h2><p className="mt-4 max-w-lg text-sm leading-6 text-[var(--muted-foreground)]">Keep your language choices, voice settings, and finished exports together—so you can focus on the story, not the process.</p></div>
        <div className="grid w-full gap-3 sm:grid-cols-3 md:max-w-xl"><div className="rounded-2xl border border-[var(--border)] bg-white/70 p-4"><Upload size={17} className="mb-5 text-[var(--accent)]"/><p className="text-sm font-semibold">Simple setup</p><p className="mt-1 text-xs leading-5 text-[var(--muted-foreground)]">Start with the media you already have.</p></div><div className="rounded-2xl border border-[var(--border)] bg-white/70 p-4"><Languages size={17} className="mb-5 text-[var(--accent)]"/><p className="text-sm font-semibold">Language choices</p><p className="mt-1 text-xs leading-5 text-[var(--muted-foreground)]">Make content for more listeners.</p></div><div className="rounded-2xl border border-[var(--border)] bg-white/70 p-4"><Headphones size={17} className="mb-5 text-[var(--accent)]"/><p className="text-sm font-semibold">Review your dub</p><p className="mt-1 text-xs leading-5 text-[var(--muted-foreground)]">Listen, refine, and export.</p></div></div>
      </section>

      <footer className="border-t border-[var(--border)] bg-white/45"><div className="mx-auto flex max-w-7xl flex-col gap-4 px-5 py-7 text-xs text-[var(--muted-foreground)] sm:flex-row sm:items-center sm:justify-between sm:px-8 lg:px-12"><Link href="/" className="flex items-center gap-2 font-semibold text-[var(--foreground)]"><span className="flex h-7 w-7 items-center justify-center rounded-lg bg-[var(--accent)] text-white"><Waves size={14}/></span>voxa<span className="text-[var(--accent)]">.</span></Link><span>Make your story heard in more languages.</span><Link href="/sign-in" className="font-medium text-[var(--foreground)] hover:text-[var(--accent)]">Open the studio <ArrowRight size={13} className="ml-1 inline"/></Link></div></footer>
    </main>
  );
}
