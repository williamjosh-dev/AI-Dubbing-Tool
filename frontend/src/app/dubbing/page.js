'use client';

import { useMemo, useState } from 'react';
import Link from 'next/link';
import {
    ArrowRight,
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

const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL || '';

const sourceLanguages = [
    { label: 'English', value: 'en' },
    { label: 'Spanish', value: 'es' },
    { label: 'French', value: 'fr' },
    { label: 'German', value: 'de' },
    { label: 'Hindi', value: 'hi' },
];

const targetLanguages = [
    { label: 'Spanish', value: 'es' },
    { label: 'French', value: 'fr' },
    { label: 'Arabic', value: 'ar' },
    { label: 'Portuguese', value: 'pt' },
    { label: 'Japanese', value: 'ja' },
];

const voiceMethods = [
    { label: 'Zonos 2 voice cloning', value: 'zonos2' },
];

const exportFormats = [
    { label: 'WAV', value: 'wav' },
    { label: 'MP3', value: 'mp3' },
];

const dubbingSteps = [
    { title: 'Upload a file', detail: 'Drop audio or video into the browser and send it to the backend.' },
    { title: 'Pick the language pair', detail: 'Choose the source and target languages before processing.' },
    { title: 'Generate the dub', detail: 'The backend transcribes, translates, synthesizes, and returns download links.' },
];

const qualityOptions = [
    { label: 'Transcription', value: 'Local Whisper', tone: 'text-emerald-700 bg-emerald-50 ring-emerald-200' },
    { label: 'Translation', value: 'Segmented', tone: 'text-sky-700 bg-sky-50 ring-sky-200' },
    { label: 'Output', value: 'Audio + video', tone: 'text-amber-700 bg-amber-50 ring-amber-200' },
];

const quickStats = [
    { label: 'API', value: 'Connected', tone: 'bg-emerald-50 text-emerald-700 ring-emerald-200' },
    { label: 'Backend', value: 'FastAPI', tone: 'bg-indigo-50 text-indigo-700 ring-indigo-200' },
    { label: 'Mode', value: 'Live upload', tone: 'bg-slate-100 text-slate-700 ring-slate-200' },
];

function buildMediaUrl(path) {
    if (!path) return '';
    if (/^https?:\/\//i.test(path)) return path;
    return API_BASE_URL ? `${API_BASE_URL}${path}` : path;
}

function formatError(error) {
    if (!error) return 'Something went wrong while processing the file.';
    if (typeof error === 'string') return error;
    if (Array.isArray(error)) return error.map((item) => item?.msg || item?.message || String(item)).join(', ');
    return error.detail || error.message || JSON.stringify(error);
}

export default function DubbingPage() {
    const [selectedFile, setSelectedFile] = useState(null);
    const [selectedSource, setSelectedSource] = useState('en');
    const [selectedTarget, setSelectedTarget] = useState('es');
    const [selectedVoiceMethod, setSelectedVoiceMethod] = useState('');
    const [selectedFormat, setSelectedFormat] = useState('wav');
    const [enhanceAudio, setEnhanceAudio] = useState(true);
    const [voiceClone, setVoiceClone] = useState(false);
    const [isSubmitting, setIsSubmitting] = useState(false);
    const [jobStatus, setJobStatus] = useState(''); // Tracking background task status
    const [result, setResult] = useState(null);
    const [error, setError] = useState('');

    const projectSummary = useMemo(
        () => [
            { label: 'Source language', value: sourceLanguages.find((item) => item.value === selectedSource)?.label || selectedSource },
            { label: 'Target language', value: targetLanguages.find((item) => item.value === selectedTarget)?.label || selectedTarget },
            { label: 'Voice engine', value: voiceMethods.find((item) => item.value === selectedVoiceMethod)?.label || 'Auto' },
            { label: 'Export format', value: selectedFormat.toUpperCase() },
        ],
        [selectedSource, selectedTarget, selectedVoiceMethod, selectedFormat]
    );

    const handleFileChange = (event) => {
        const file = event.target.files?.[0] || null;
        setSelectedFile(file);
        setError('');
        setResult(null);
        setJobStatus('');
    };

    const handleSubmit = async () => {
        if (!selectedFile) {
            setError('Choose an audio or video file before starting the dub.');
            return;
        }

        setIsSubmitting(true);
        setError('');
        setResult(null);
        setJobStatus('Queuing job...');

        try {
            const formData = new FormData();
            formData.append('audioFile', selectedFile);
            formData.append('srcLang', selectedSource);
            formData.append('tgtLang', selectedTarget);
            formData.append('voiceClone', voiceClone ? 'on' : 'off');
            formData.append('voiceMethod', selectedVoiceMethod);
            formData.append('outputFormat', selectedFormat);
            formData.append('enhanceAudio', enhanceAudio ? 'on' : 'off');

            // 1. Send file to initiate background processing
            const response = await fetch(`${API_BASE_URL}/api/dub`, {
                method: 'POST',
                body: formData,
            });

            const data = await response.json();

            if (!response.ok) {
                throw new Error(formatError(data));
            }

            const jobId = data.jobId;
            setJobStatus('Processing dubbing task...');

            // 2. Poll the status endpoint until complete or failed
            await new Promise((resolve, reject) => {
                const pollInterval = setInterval(async () => {
                    try {
                        const statusRes = await fetch(`${API_BASE_URL}/api/status/${jobId}`);
                        const jobData = await statusRes.json();

                        if (!statusRes.ok) {
                            clearInterval(pollInterval);
                            reject(new Error(formatError(jobData)));
                            return;
                        }

                        if (jobData.status === 'completed') {
                            clearInterval(pollInterval);
                            setResult(jobData.result);
                            setJobStatus('');
                            resolve();
                        } else if (jobData.status === 'failed') {
                            clearInterval(pollInterval);
                            reject(new Error(jobData.error || 'Dubbing processing failed on backend.'));
                        } else {
                            setJobStatus(`Status: ${jobData.status}...`);
                        }
                    } catch (pollErr) {
                        clearInterval(pollInterval);
                        reject(pollErr);
                    }
                }, 3000); // Check every 3 seconds
            });

        } catch (submitError) {
            setError(submitError instanceof Error ? submitError.message : 'Failed to submit the job.');
            setJobStatus('');
        } finally {
            setIsSubmitting(false);
        }
    };
            const audioUrl = result?.audioUrl ? buildMediaUrl(result.audioUrl) : '';
            const videoUrl = result?.videoUrl ? buildMediaUrl(result.videoUrl) : '';
            const transcriptUrl = result?.transcriptUrl ? buildMediaUrl(result.transcriptUrl) : '';
    return (
        <form
            className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8"
            onSubmit={(event) => {
                event.preventDefault();
                handleSubmit();
            }}
        >
            <input
                id="dubbing-upload-input"
                type="file"
                accept="video/*,audio/*"
                className="sr-only"
                aria-label="Upload audio or video file"
                onChange={handleFileChange}
            />

            <header className="hero-shell text-white">
                <div className="absolute inset-0 opacity-30 [background-image:radial-gradient(circle_at_top_right,rgba(99,102,241,0.55),transparent_34%),radial-gradient(circle_at_bottom_left,rgba(56,189,248,0.2),transparent_28%)]" />
                <div className="relative max-w-3xl">
                    <p className="beta-pill w-fit">Live FastAPI upload</p>
                    <h1 className="mt-4 text-3xl font-semibold sm:text-4xl">Upload a file and generate the dub</h1>
                    <p className="mt-3 text-sm text-slate-300 sm:text-base">
                        Pick your languages and TTS engine, send the file to the backend, and get back downloadable audio, transcript,
                        and video links when the source is a video.
                    </p>
                    {jobStatus && (
                        <p className="mt-2 text-sm text-amber-300 animate-pulse font-medium">
                            {jobStatus}
                        </p>
                    )}

                    <div className="mt-6 flex flex-wrap gap-3">
                        <label htmlFor="dubbing-upload-input" className="inline-flex cursor-pointer items-center gap-2 rounded-lg bg-white px-5 py-2.5 text-sm font-semibold text-slate-900 shadow-sm transition hover:bg-slate-100">
                            <UploadCloud className="h-4 w-4" />
                            Browse file
                        </label>
                        <button
                            type="submit"
                            disabled={isSubmitting}
                            className="inline-flex items-center gap-2 rounded-lg border border-white/20 bg-white/10 px-5 py-2.5 text-sm font-semibold text-white transition hover:bg-white/20 disabled:cursor-not-allowed disabled:opacity-60"
                        >
                            {isSubmitting ? 'Processing...' : 'Start dubbing'}
                            <ArrowRight className="h-4 w-4" />
                        </button>
                    </div>
                </div>
            </header>

            <div className="mt-8 grid grid-cols-1 gap-6 lg:grid-cols-12">
                <main className="lg:col-span-8 space-y-6">
                    <section className="panel">
                        <div className="flex items-center justify-between gap-4">
                            <div className="flex items-center gap-3">
                                <UploadCloud className="h-5 w-5 text-indigo-600" />
                                <h2 className="text-lg font-semibold text-slate-900">Upload workspace</h2>
                            </div>
                            <span className="inline-flex items-center rounded-full bg-slate-100 px-3 py-1 text-sm font-medium text-slate-700">
                                {selectedFile ? selectedFile.name : 'No file selected'}
                            </span>
                        </div>

                        <label htmlFor="dubbing-upload-input" className="mt-4 block cursor-pointer upload-dropzone">
                            <div className="mx-auto flex h-12 w-12 items-center justify-center rounded-full bg-indigo-600/10 text-indigo-600">
                                <Clapperboard className="h-6 w-6" />
                            </div>
                            <p className="mt-4 text-lg font-semibold text-slate-900">Drop your audio or video here</p>
                            <p className="mt-2 text-sm text-slate-500">
                                The selected file will be posted to the backend as multipart form data and processed end to end.
                            </p>

                            <div className="mt-5 grid grid-cols-1 gap-4 sm:grid-cols-3">
                                <div className="flex flex-col items-center justify-center rounded-lg bg-white p-4 text-center ring-1 ring-slate-100">
                                    <div className="flex h-12 w-12 items-center justify-center rounded-full bg-indigo-600/10 text-indigo-600">
                                        <FileAudio2 className="h-6 w-6" />
                                    </div>
                                    <p className="mt-3 font-medium text-slate-900">Upload file</p>
                                    <p className="mt-1 text-xs text-slate-500">MP4, MOV, MP3, WAV, and more</p>
                                </div>

                                <div className="flex flex-col items-center justify-center rounded-lg bg-white p-4 text-center ring-1 ring-slate-100">
                                    <div className="flex h-12 w-12 items-center justify-center rounded-full bg-sky-600/10 text-sky-600">
                                        <Sparkles className="h-6 w-6" />
                                    </div>
                                    <p className="mt-3 font-medium text-slate-900">Translate</p>
                                    <p className="mt-1 text-xs text-slate-500">Segmented transcription and translation</p>
                                </div>

                                <div className="flex flex-col items-center justify-center rounded-lg bg-white p-4 text-center ring-1 ring-slate-100">
                                    <div className="flex h-12 w-12 items-center justify-center rounded-full bg-emerald-600/10 text-emerald-600">
                                        <ShieldCheck className="h-6 w-6" />
                                    </div>
                                    <p className="mt-3 font-medium text-slate-900">Download</p>
                                    <p className="mt-1 text-xs text-slate-500">Audio, transcript, and optional video</p>
                                </div>
                            </div>

                            <p className="mt-4 text-xs text-slate-400">
                                Click Browse file to choose a local clip, then press Start dubbing.
                            </p>
                        </label>

                        <div className="mt-6 grid grid-cols-1 gap-4 md:grid-cols-2">
                            <div className="panel-soft">
                                <div className="flex items-center gap-2 text-sm font-semibold text-slate-900">
                                    <Music2 className="h-4 w-4 text-indigo-600" />
                                    Voice engine
                                </div>
                                <div className="mt-3 flex flex-wrap gap-2">
                                    {voiceMethods.map((method) => (
                                        <button
                                            key={method.label}
                                            type="button"
                                            onClick={() => setSelectedVoiceMethod(method.value)}
                                            className={`rounded-full px-3 py-1.5 text-sm font-medium transition ${selectedVoiceMethod === method.value
                                                ? 'bg-indigo-600 text-white shadow-sm'
                                                : 'bg-white text-slate-600 ring-1 ring-inset ring-slate-200 hover:bg-slate-100'
                                                }`}
                                        >
                                            {method.label}
                                        </button>
                                    ))}
                                </div>
                            </div>

                            <div className="panel-soft">
                                <div className="flex items-center gap-2 text-sm font-semibold text-slate-900">
                                    <Settings2 className="h-4 w-4 text-indigo-600" />
                                    Export format
                                </div>
                                <div className="mt-3 flex flex-wrap gap-2">
                                    {exportFormats.map((format) => (
                                        <button
                                            key={format.label}
                                            type="button"
                                            onClick={() => setSelectedFormat(format.value)}
                                            className={`rounded-full px-3 py-1.5 text-sm font-medium transition ${selectedFormat === format.value
                                                ? 'bg-slate-900 text-white shadow-sm'
                                                : 'bg-white text-slate-600 ring-1 ring-inset ring-slate-200 hover:bg-slate-100'
                                                }`}
                                        >
                                            {format.label}
                                        </button>
                                    ))}
                                </div>
                            </div>
                        </div>

                        <div className="mt-6 grid grid-cols-1 gap-4 md:grid-cols-2">
                            <label className="block rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
                                <span className="flex items-center gap-2 text-sm font-semibold text-slate-900">
                                    <Languages className="h-4 w-4 text-indigo-600" />
                                    Source language
                                </span>
                                <select
                                    value={selectedSource}
                                    onChange={(event) => setSelectedSource(event.target.value)}
                                    className="mt-3 w-full rounded-lg border border-slate-200 bg-white px-3 py-2.5 text-sm text-slate-700 focus:border-indigo-400 focus:outline-none focus:ring-2 focus:ring-indigo-100"
                                >
                                    {sourceLanguages.map((language) => (
                                        <option key={language.value} value={language.value}>
                                            {language.label}
                                        </option>
                                    ))}
                                </select>
                            </label>

                            <label className="block rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
                                <span className="flex items-center gap-2 text-sm font-semibold text-slate-900">
                                    <Languages className="h-4 w-4 text-indigo-600" />
                                    Target language
                                </span>
                                <select
                                    value={selectedTarget}
                                    onChange={(event) => setSelectedTarget(event.target.value)}
                                    className="mt-3 w-full rounded-lg border border-slate-200 bg-white px-3 py-2.5 text-sm text-slate-700 focus:border-indigo-400 focus:outline-none focus:ring-2 focus:ring-indigo-100"
                                >
                                    {targetLanguages.map((language) => (
                                        <option key={language.value} value={language.value}>
                                            {language.label}
                                        </option>
                                    ))}
                                </select>
                            </label>
                        </div>

                        <div className="mt-6 grid grid-cols-1 gap-4 md:grid-cols-2">
                            <label className="panel-soft flex items-center justify-between gap-4">
                                <div>
                                    <p className="text-sm font-semibold text-slate-900">Enhance audio</p>
                                    <p className="mt-1 text-sm text-slate-500">Normalize and clean the source before transcription.</p>
                                </div>
                                <input
                                    type="checkbox"
                                    checked={enhanceAudio}
                                    onChange={(event) => setEnhanceAudio(event.target.checked)}
                                    className="h-5 w-5 rounded border-slate-300 text-indigo-600 focus:ring-indigo-500"
                                />
                            </label>

                            <label className="panel-soft flex items-center justify-between gap-4">
                                <div>
                                    <p className="text-sm font-semibold text-slate-900">Voice clone</p>
                                    <p className="mt-1 text-sm text-slate-500">Sent through as a flag for future voice-clone support.</p>
                                </div>
                                <input
                                    type="checkbox"
                                    checked={voiceClone}
                                    onChange={(event) => setVoiceClone(event.target.checked)}
                                    className="h-5 w-5 rounded border-slate-300 text-indigo-600 focus:ring-indigo-500"
                                />
                            </label>
                        </div>

                        <div className="mt-6 flex flex-wrap items-center gap-3">
                            <button
                                type="submit"
                                disabled={isSubmitting}
                                className="btn-primary"
                            >
                                <WandSparkles className="h-4 w-4" />
                                {isSubmitting ? 'Processing...' : 'Start dubbing workflow'}
                            </button>
                            <p className="text-sm text-slate-500">The response comes back with live download links from FastAPI.</p>
                        </div>

                        {error && (
                            <div className="mt-5 rounded-xl border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-800">
                                {error}
                            </div>
                        )}

                        {result && result.warnings?.length > 0 && (
                            <div className="mt-5 rounded-xl border border-amber-200 bg-amber-50 px-4 py-3 text-sm text-amber-900">
                                {result.warnings.join(' ')}
                            </div>
                        )}
                    </section>

                    <section className="grid grid-cols-1 gap-4 md:grid-cols-2">
                        <div className="panel">
                            <div className="flex items-center gap-2">
                                <Globe2 className="h-5 w-5 text-indigo-600" />
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

                        <div className="panel">
                            <div className="flex items-center gap-2 text-sm font-semibold text-slate-900">
                                <SlidersHorizontal className="h-5 w-5 text-indigo-600" />
                                Project summary
                            </div>
                            <div className="mt-4 space-y-2">
                                {projectSummary.map((item) => (
                                    <div key={item.label} className="flex items-center justify-between gap-4 text-sm">
                                        <span className="text-slate-500">{item.label}</span>
                                        <span className="font-medium text-slate-900">{item.value}</span>
                                    </div>
                                ))}
                            </div>

                            <div className="mt-5 space-y-2">
                                {qualityOptions.map((option) => (
                                    <div key={option.label} className={`flex items-center justify-between rounded-lg px-3 py-2 ring-1 ring-inset ${option.tone}`}>
                                        <span className="text-sm font-medium">{option.label}</span>
                                        <span className="text-sm font-semibold">{option.value}</span>
                                    </div>
                                ))}
                            </div>
                        </div>
                    </section>
                </main>

                <aside className="lg:col-span-4 space-y-6">
                    <div className="sticky top-24 space-y-6">
                        <div className="bg-slate-950 rounded-lg p-6 text-white shadow-inner">
                            <div className="flex items-center gap-2">
                                <PlayCircle className="h-5 w-5 text-indigo-400" />
                                <h3 className="text-lg font-semibold">Result preview</h3>
                            </div>

                            <div className="mt-4 space-y-3 text-sm text-slate-300">
                                <div className="flex items-center justify-between text-xs text-slate-400">
                                    <span>Status</span>
                                    <span>{isSubmitting ? 'Processing' : result ? 'Complete' : 'Waiting'}</span>
                                </div>
                                <div className="h-40 rounded-lg border border-white/10 bg-gradient-to-br from-slate-800 via-slate-900 to-indigo-950" />
                                <p className="text-slate-300">
                                    {result ? 'Downloads are ready below.' : 'Start a job to see the generated files and transcript summary.'}
                                </p>
                            </div>
                        </div>

                        <div className="panel">
                            <p className="text-sm font-semibold text-slate-900">Quick status</p>
                            <div className="mt-3 flex flex-wrap gap-2">
                                {quickStats.map((item) => (
                                    <span key={item.label} className={`summary-chip ${item.tone}`}>
                                        {item.label}: {item.value}
                                    </span>
                                ))}
                            </div>
                        </div>

                        <div className="panel">
                            <p className="text-sm font-semibold text-slate-900">Download links</p>
                            <div className="mt-3 space-y-3 text-sm">
                                {audioUrl ? (
                                    <a className="block rounded-lg border border-slate-200 px-4 py-3 font-medium text-indigo-700 hover:bg-indigo-50" href={audioUrl} target="_blank" rel="noreferrer">
                                        Download dubbed audio
                                    </a>
                                ) : (
                                    <div className="rounded-lg border border-slate-200 px-4 py-3 text-slate-400">Audio will appear here after processing.</div>
                                )}

                                {videoUrl ? (
                                    <a className="block rounded-lg border border-slate-200 px-4 py-3 font-medium text-indigo-700 hover:bg-indigo-50" href={videoUrl} target="_blank" rel="noreferrer">
                                        Download dubbed video
                                    </a>
                                ) : null}

                                {transcriptUrl ? (
                                    <a className="block rounded-lg border border-slate-200 px-4 py-3 font-medium text-indigo-700 hover:bg-indigo-50" href={transcriptUrl} target="_blank" rel="noreferrer">
                                        Download transcript
                                    </a>
                                ) : null}
                            </div>
                        </div>

                        {result?.translatedText ? (
                            <div className="panel">
                                <p className="text-sm font-semibold text-slate-900">Translated text</p>
                                <p className="mt-3 text-sm text-slate-600">{result.translatedText}</p>
                                <p className="mt-3 text-xs text-slate-400">
                                    {result.translatedSegments?.length || 0} translated segments returned by the backend.
                                </p>
                            </div>
                        ) : null}

                        {audioUrl ? (
                            <div className="panel">
                                <p className="text-sm font-semibold text-slate-900">Playback</p>
                                <audio className="mt-3 w-full" controls src={audioUrl} />
                                {videoUrl ? <video className="mt-4 w-full rounded-lg border border-slate-200" controls src={videoUrl} /> : null}
                            </div>
                        ) : null}
                    </div>
                </aside>
            </div>
        </form>
    );
}
    