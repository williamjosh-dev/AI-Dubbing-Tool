'use client';

import { useMemo, useState } from 'react';
import Link from 'next/link';
import {
    ArrowRight,
    CheckCircle2,
    Clapperboard,
    FileAudio2,
    Globe2,
    Languages,
    Music2,
    PlayCircle,
    Settings2,
    Sparkles,
    UploadCloud,
    ShieldCheck,
    SlidersHorizontal,
    WandSparkles,
} from 'lucide-react';

const sourceLanguages = ['English', 'Spanish', 'French', 'German', 'Hindi'];
const targetLanguages = ['Spanish', 'French', 'Arabic', 'Portuguese', 'Japanese'];
const voiceStyles = ['Natural', 'Energetic', 'Cinematic', 'Warm'];
const exportFormats = ['MP4', 'MOV', 'WAV'];

const dubbingSteps = [
    {
        title: 'Upload a video',
        detail: 'Drop a video file into the workspace or browse your files to begin.',
    },
    {
        title: 'Pick the language pair',
        detail: 'Choose the source language and the language you want the dub rendered in.',
    },
    {
        title: 'Adjust delivery settings',
        detail: 'Set the voice style, speed, and export format before processing later.',
    },
];

const qualityOptions = [
    { label: 'Voice alignment', value: 'High', tone: 'text-emerald-700 bg-emerald-50 ring-emerald-200' },
    { label: 'Subtitle track', value: 'Enabled', tone: 'text-sky-700 bg-sky-50 ring-sky-200' },
    { label: 'Lip sync', value: 'Preview', tone: 'text-amber-700 bg-amber-50 ring-amber-200' },
];

const betaHighlights = [
    'Upload flow is ready for test users.',
    'Language and voice presets can be exercised without backend wiring.',
    'Preview cards show what will be powered by the pipeline later.',
];

const quickStats = [
    { label: 'Upload status', value: 'Ready', tone: 'bg-emerald-50 text-emerald-700 ring-emerald-200' },
    { label: 'Backend', value: 'Not connected', tone: 'bg-slate-100 text-slate-700 ring-slate-200' },
    { label: 'Beta mode', value: 'On', tone: 'bg-indigo-50 text-indigo-700 ring-indigo-200' },
];

export default function DubbingPage() {
    const [selectedSource, setSelectedSource] = useState('English');
    const [selectedTarget, setSelectedTarget] = useState('Spanish');
    const [selectedVoice, setSelectedVoice] = useState('Natural');
    const [selectedFormat, setSelectedFormat] = useState('MP4');
    const [selectedFile, setSelectedFile] = useState('No file selected yet');

    const projectSummary = useMemo(
        () => [
            { label: 'Source language', value: selectedSource },
            { label: 'Target language', value: selectedTarget },
            { label: 'Voice style', value: selectedVoice },
            { label: 'Export format', value: selectedFormat },
        ],
        [selectedSource, selectedTarget, selectedVoice, selectedFormat]
    );

    const handleFileChange = (event) => {
        const file = event.target.files?.[0];
        setSelectedFile(file ? file.name : 'No file selected yet');
    };

    return (
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
            {/* Hero */}
            <header className="bg-slate-900 rounded-xl p-8 text-white">
                <div className="max-w-3xl">
                    <h1 className="text-3xl font-semibold sm:text-4xl">Upload a video and prepare the dub</h1>
                    <p className="mt-3 text-sm text-slate-300 sm:text-base">
                        Upload your video, choose source and target languages, pick a voice style, and export a dubbed version.
                        Preview everything locally before you process or download.
                    </p>

                    <div className="mt-6 flex flex-wrap gap-3">
                        <label className="inline-flex cursor-pointer items-center gap-2 rounded-lg bg-white px-5 py-2.5 text-sm font-semibold text-slate-900 shadow-sm transition hover:bg-slate-100">
                            <UploadCloud className="h-4 w-4" />
                            Browse files
                            <input type="file" accept="video/*" className="hidden" onChange={handleFileChange} />
                        </label>
                        <Link
                            href="/dashboard"
                            className="inline-flex items-center gap-2 rounded-lg border border-white/20 bg-white/10 px-5 py-2.5 text-sm font-semibold text-white transition hover:bg-white/20"
                        >
                            View dashboard
                            <ArrowRight className="h-4 w-4" />
                        </Link>
                    </div>
                </div>
            </header>

            {/* Main workspace: 12-column grid (left 8 / right 4) */}
            <div className="mt-8 grid grid-cols-1 lg:grid-cols-12 gap-6">
                {/* Left main column (approx 66%) */}
                <main className="lg:col-span-8 space-y-6">
                    {/* Upload workspace card */}
                    <section className="bg-white rounded-lg p-6 shadow-sm border border-slate-200">
                        <div className="flex items-center justify-between">
                            <div className="flex items-center gap-3">
                                <UploadCloud className="h-5 w-5 text-indigo-600" />
                                <h2 className="text-lg font-semibold text-slate-900">Upload workspace</h2>
                            </div>
                            <span className="inline-flex items-center rounded-full bg-slate-100 px-3 py-1 text-sm font-medium text-slate-700">Preview mode</span>
                        </div>

                        <div className="mt-4">
                            <div className="mx-auto flex h-12 w-12 items-center justify-center rounded-full bg-indigo-600/10 text-indigo-600">
                                <Clapperboard className="h-6 w-6" />
                            </div>
                            <p className="mt-4 text-lg font-semibold text-slate-900">Drop your video here</p>
                            <p className="mt-2 text-sm text-slate-500">
                                Upload your video to preview the dubbing workflow. Nothing is sent to a server until you start
                                processing.
                            </p>
                            <div className="mt-5">
                                <input
                                    id="file-input"
                                    type="file"
                                    accept="video/*,audio/*"
                                    className="hidden"
                                    onChange={handleFileChange}
                                />

                                <label htmlFor="file-input" className="group block cursor-pointer rounded-lg border-2 border-dashed border-slate-200 p-6 hover:border-indigo-500">
                                    <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
                                        <div className="flex flex-col items-center justify-center rounded-lg bg-slate-50 p-4 text-center">
                                            <div className="flex h-12 w-12 items-center justify-center rounded-full bg-indigo-600/10 text-indigo-600">
                                                <FileAudio2 className="h-6 w-6" />
                                            </div>
                                            <p className="mt-3 font-medium text-slate-900">Upload a file</p>
                                            <p className="mt-1 text-xs text-slate-500">Video, audio, or music (MP4, MOV, MP3, WAV)</p>
                                        </div>

                                        <div className="flex flex-col items-center justify-center rounded-lg bg-white p-4 text-center ring-1 ring-slate-100">
                                            <div className="text-indigo-600">🎵</div>
                                            <p className="mt-3 font-medium text-slate-900">Try a sample</p>
                                            <p className="mt-1 text-xs text-slate-500">Preview with example audio</p>
                                        </div>

                                        <div className="flex flex-col items-center justify-center rounded-lg bg-white p-4 text-center ring-1 ring-slate-100">
                                            <div className="text-indigo-600">🔗</div>
                                            <p className="mt-3 font-medium text-slate-900">Paste URL</p>
                                            <p className="mt-1 text-xs text-slate-500">Use a remote file for quick testing</p>
                                        </div>
                                    </div>

                                    <p className="mt-4 text-xs text-slate-400">Click the box to select a file from your device. Accepted: video and audio files.</p>
                                </label>

                                <p className="mt-3 text-xs text-slate-400">Selected file: {selectedFile === 'No file selected yet' ? 'No file selected' : selectedFile}</p>
                            </div>
                        </div>

                        <div className="mt-6 grid grid-cols-1 md:grid-cols-2 gap-4">
                            <div className="bg-white rounded-lg p-6 shadow-sm border border-slate-200">
                                <div className="flex items-center gap-2 text-sm font-semibold text-slate-900">
                                    <Music2 className="h-4 w-4 text-indigo-600" />
                                    Voice style
                                </div>
                                <div className="mt-3 flex flex-wrap gap-2">
                                    {voiceStyles.map((voice) => (
                                        <button
                                            key={voice}
                                            type="button"
                                            onClick={() => setSelectedVoice(voice)}
                                            className={`rounded-full px-3 py-1.5 text-sm font-medium transition ${selectedVoice === voice
                                                    ? 'bg-indigo-600 text-white shadow-sm'
                                                    : 'bg-white text-slate-600 ring-1 ring-inset ring-slate-200 hover:bg-slate-100'
                                                }`}
                                        >
                                            {voice}
                                        </button>
                                    ))}
                                </div>
                            </div>

                            <div className="bg-white rounded-lg p-6 shadow-sm border border-slate-200">
                                <div className="flex items-center gap-2 text-sm font-semibold text-slate-900">
                                    <Settings2 className="h-4 w-4 text-indigo-600" />
                                    Export format
                                </div>
                                <div className="mt-3 flex flex-wrap gap-2">
                                    {exportFormats.map((format) => (
                                        <button
                                            key={format}
                                            type="button"
                                            onClick={() => setSelectedFormat(format)}
                                            className={`rounded-full px-3 py-1.5 text-sm font-medium transition ${selectedFormat === format
                                                    ? 'bg-slate-900 text-white shadow-sm'
                                                    : 'bg-white text-slate-600 ring-1 ring-inset ring-slate-200 hover:bg-slate-100'
                                                }`}
                                        >
                                            {format}
                                        </button>
                                    ))}
                                </div>
                            </div>
                        </div>
                    </section>

                    <section className="grid grid-cols-1 md:grid-cols-2 gap-4">
                        <div className="bg-white rounded-lg p-6 shadow-sm border border-slate-200">
                            <div className="flex items-center gap-2">
                                <Languages className="h-5 w-5 text-indigo-600" />
                                <h2 className="text-lg font-semibold text-slate-900">Language pair</h2>
                            </div>

                            <div className="mt-4 space-y-4">
                                <label className="block">
                                    <span className="text-sm font-medium text-slate-600">Source language</span>
                                    <select
                                        value={selectedSource}
                                        onChange={(event) => setSelectedSource(event.target.value)}
                                        className="mt-2 w-full rounded-lg border border-slate-200 bg-white px-3 py-2.5 text-sm text-slate-700 focus:border-indigo-400 focus:outline-none focus:ring-2 focus:ring-indigo-100"
                                    >
                                        {sourceLanguages.map((language) => (
                                            <option key={language} value={language}>
                                                {language}
                                            </option>
                                        ))}
                                    </select>
                                </label>

                                <label className="block">
                                    <span className="text-sm font-medium text-slate-600">Target language</span>
                                    <select
                                        value={selectedTarget}
                                        onChange={(event) => setSelectedTarget(event.target.value)}
                                        className="mt-2 w-full rounded-lg border border-slate-200 bg-white px-3 py-2.5 text-sm text-slate-700 focus:border-indigo-400 focus:outline-none focus:ring-2 focus:ring-indigo-100"
                                    >
                                        {targetLanguages.map((language) => (
                                            <option key={language} value={language}>
                                                {language}
                                            </option>
                                        ))}
                                    </select>
                                </label>
                            </div>
                        </div>

                        <div className="bg-white rounded-lg p-6 shadow-sm border border-slate-200">
                            <div className="flex items-center gap-2">
                                <SlidersHorizontal className="h-5 w-5 text-indigo-600" />
                                <h2 className="text-lg font-semibold text-slate-900">Processing notes</h2>
                            </div>

                            <div className="mt-4 space-y-3">
                                {dubbingSteps.map((step, index) => (
                                    <div key={step.title} className="rounded-lg border border-slate-100 bg-slate-50 p-4">
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
                    </section>
                </main>

                {/* Right column (approx 33%) */}
                <aside className="lg:col-span-4">
                    <div className="sticky top-24 space-y-6">
                        <div className="bg-slate-950 rounded-lg p-6 text-white shadow-inner">
                            <div className="flex items-center gap-2">
                                <PlayCircle className="h-5 w-5 text-indigo-400" />
                                <h3 className="text-lg font-semibold">Preview panel</h3>
                            </div>

                            <div className="mt-4">
                                <div className="flex items-center justify-between text-xs text-slate-400">
                                    <span>Preview timeline</span>
                                    <span>00:00 / 00:00</span>
                                </div>
                                <div className="mt-4 h-40 rounded-lg border border-white/10 bg-gradient-to-br from-slate-800 via-slate-900 to-indigo-950" />
                                <div className="mt-4 flex items-center justify-between text-sm text-slate-300">
                                    <span>Video placeholder</span>
                                    <span>Audio layers ready</span>
                                </div>
                            </div>
                        </div>

                        <div className="bg-white rounded-lg p-6 shadow-sm border border-slate-200">
                            <p className="text-sm font-semibold text-slate-900">Project summary</p>
                            <div className="mt-3 space-y-2">
                                {projectSummary.map((item) => (
                                    <div key={item.label} className="flex items-center justify-between gap-4 text-sm">
                                        <span className="text-slate-500">{item.label}</span>
                                        <span className="font-medium text-slate-900">{item.value}</span>
                                    </div>
                                ))}
                            </div>
                        </div>

                        <div className="bg-white rounded-lg p-6 shadow-sm border border-slate-200">
                            <div className="flex items-center gap-2 text-sm font-semibold text-slate-900">
                                <Globe2 className="h-4 w-4 text-indigo-600" />
                                Quality controls
                            </div>
                            <div className="mt-3 space-y-2">
                                {qualityOptions.map((option) => (
                                    <div key={option.label} className={`flex items-center justify-between rounded-lg px-3 py-2 ring-1 ring-inset ${option.tone}`}>
                                        <span className="text-sm font-medium">{option.label}</span>
                                        <span className="text-sm font-semibold">{option.value}</span>
                                    </div>
                                ))}
                            </div>
                        </div>

                        <div className="grid gap-3 sm:grid-cols-2">
                            {sourceLanguages.slice(0, 2).map((language, index) => (
                                <div key={language} className="rounded-lg border border-slate-200 bg-white p-4 shadow-sm">
                                    <div className="flex items-center gap-2 text-sm font-semibold text-slate-900">
                                        <CheckCircle2 className="h-4 w-4 text-emerald-600" />
                                        Ready slot {index + 1}
                                    </div>
                                    <p className="mt-2 text-sm text-slate-500">{language} source preset</p>
                                </div>
                            ))}
                        </div>

                        <button
                            type="button"
                            className="mt-2 w-full rounded-lg bg-slate-900 px-5 py-3 text-sm font-semibold text-white shadow-sm hover:bg-slate-800"
                        >
                            <Clapperboard className="h-4 w-4 inline-block mr-2" />
                            Start dubbing workflow
                        </button>
                    </div>
                </aside>
            </div>
        </div>
    );
}
    