'use client';

import { useEffect, useState } from 'react';
import Link from 'next/link';
import { ArrowLeft, CheckCircle2, Download, FileAudio2, FileVideo2, LoaderCircle, Sparkles, XCircle } from 'lucide-react';
import { clearDubbingDraft, getDubbingDraft } from '../project-store';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL || '';
const ACTIVE_JOB_STORAGE_KEY = 'ai-dubbing-active-job';

function formatError(error) {
    if (!error) return 'Something went wrong while processing the file.';
    if (typeof error === 'string') return error;
    if (Array.isArray(error)) return error.map((item) => item?.msg || item?.message || String(item)).join(', ');
    return error.detail || error.message || JSON.stringify(error);
}

function buildMediaUrl(path) {
    if (!path) return '';
    if (/^https?:\/\//i.test(path)) return path;
    return API_BASE_URL ? `${API_BASE_URL}${path}` : path;
}

function startJobPolling(jobId, { onStatus, onComplete, onFailure }) {
    let isCancelled = false;
    let timeoutId;

    const checkStatus = async () => {
        try {
            const response = await fetch(`${API_BASE_URL}/api/status/${jobId}`);
            const data = await response.json();
            if (!response.ok) throw new Error(formatError(data));
            if (isCancelled) return;

            if (data.status === 'completed') {
                onComplete(data.result);
                return;
            }
            if (data.status === 'failed') {
                onFailure(new Error(data.error || 'Dubbing processing failed on the backend.'));
                return;
            }

            onStatus(data.status);
            timeoutId = window.setTimeout(checkStatus, 3000);
        } catch (error) {
            if (!isCancelled) onFailure(error);
        }
    };

    checkStatus();
    return () => {
        isCancelled = true;
        if (timeoutId) window.clearTimeout(timeoutId);
    };
}

const processingSteps = [
    { title: 'Prepare your file', detail: 'We check the file and get it ready for the dubbing process.' },
    { title: 'Pull out the original audio', detail: 'We separate the spoken sound from the video so every word can be handled clearly.' },
    { title: 'Write down what was said', detail: 'We listen to the original voice and create a time-matched written version.' },
    { title: 'Translate each part', detail: 'We turn the written words into your chosen language while keeping the timing in mind.' },
    { title: 'Create the new voice', detail: 'We generate a natural voice track from the translated words.' },
    { title: 'Finish your dubbed file', detail: 'We bring the new voice and original video together and prepare your result.' },
];

function getProcessingStage(status, isComplete) {
    if (isComplete) return processingSteps.length;
    const normalizedStatus = status.toLowerCase();
    if (normalizedStatus.includes('upload') || normalizedStatus.includes('prepar')) return 1;
    if (normalizedStatus.includes('extract') || normalizedStatus.includes('audio')) return 2;
    if (normalizedStatus.includes('transcrib') || normalizedStatus.includes('listen')) return 3;
    if (normalizedStatus.includes('translat')) return 4;
    if (normalizedStatus.includes('synth') || normalizedStatus.includes('voice') || normalizedStatus.includes('speech')) return 5;
    if (normalizedStatus.includes('assembl') || normalizedStatus.includes('render') || normalizedStatus.includes('finish')) return 6;
    return 1;
}

function formatTimestamp(seconds) {
    const totalSeconds = Math.max(0, Math.floor(Number(seconds) || 0));
    const minutes = Math.floor(totalSeconds / 60).toString().padStart(2, '0');
    const remainingSeconds = (totalSeconds % 60).toString().padStart(2, '0');
    return `${minutes}:${remainingSeconds}`;
}

export default function DubbingEditorPage() {
    const [draft, setDraft] = useState(null);
    const [jobId, setJobId] = useState('');
    const [jobStatus, setJobStatus] = useState('Preparing your editor...');
    const [result, setResult] = useState(null);
    const [editedSegments, setEditedSegments] = useState([]);
    const [error, setError] = useState('');
    const [isWorking, setIsWorking] = useState(true);
    const [isGeneratingTts, setIsGeneratingTts] = useState(false);

    useEffect(() => {
        let stopPolling;
        const activeJob = window.localStorage.getItem(ACTIVE_JOB_STORAGE_KEY);
        const savedDraft = getDubbingDraft();

        if (savedDraft) setDraft(savedDraft);

        const handleComplete = (jobResult) => {
            setResult(jobResult);
            setEditedSegments(jobResult?.translatedSegments || []);
            setJobStatus('Your dub is ready.');
            setIsWorking(false);
            window.localStorage.removeItem(ACTIVE_JOB_STORAGE_KEY);
            clearDubbingDraft();
        };
        const handleFailure = (jobError) => {
            setError(jobError instanceof Error ? jobError.message : 'Dubbing processing failed.');
            setJobStatus('The job could not be completed.');
            setIsWorking(false);
            window.localStorage.removeItem(ACTIVE_JOB_STORAGE_KEY);
        };

        if (activeJob) {
            setJobStatus('Restoring your dubbing job...');
            const savedJobId = JSON.parse(activeJob).jobId;
            setJobId(savedJobId);
            stopPolling = startJobPolling(savedJobId, {
                onStatus: (status) => setJobStatus(`Status: ${status}...`),
                onComplete: handleComplete,
                onFailure: handleFailure,
            });
        } else if (savedDraft?.selectedFile) {
            const runJob = async () => {
                try {
                    setJobStatus('Preparing upload...');
                    const tokenResponse = await fetch('/api/upload-token', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({
                            filename: savedDraft.selectedFile.name,
                            contentType: savedDraft.selectedFile.type || 'application/octet-stream',
                            size: savedDraft.selectedFile.size,
                        }),
                    });
                    const tokenData = await tokenResponse.json();
                    if (!tokenResponse.ok) throw new Error(formatError(tokenData));

                    setJobStatus('Uploading your source file...');
                    const uploadResponse = await fetch(tokenData.uploadUrl, {
                        method: 'PUT',
                        headers: { 'Content-Type': savedDraft.selectedFile.type || 'application/octet-stream' },
                        body: savedDraft.selectedFile,
                    });
                    if (!uploadResponse.ok) throw new Error('The file upload to storage failed.');

                    setJobStatus('Creating your dubbing job...');
                    const response = await fetch(`${API_BASE_URL}/api/dub-from-storage`, {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({
                            objectKey: tokenData.objectKey,
                            filename: savedDraft.selectedFile.name,
                            srcLang: savedDraft.selectedSource,
                            tgtLang: savedDraft.selectedTarget,
                            voiceClone: savedDraft.voiceClone ? 'on' : 'off',
                            voiceMethod: savedDraft.selectedVoiceMethod,
                            outputFormat: savedDraft.selectedFormat,
                            enhanceAudio: savedDraft.enhanceAudio ? 'on' : 'off',
                            betaToken: savedDraft.betaToken,
                        }),
                    });
                    const data = await response.json();
                    if (!response.ok) throw new Error(formatError(data));

                    window.localStorage.setItem(ACTIVE_JOB_STORAGE_KEY, JSON.stringify({ jobId: data.jobId }));
                    setJobId(data.jobId);
                    setJobStatus('Your dub is processing...');
                    stopPolling = startJobPolling(data.jobId, {
                        onStatus: (status) => setJobStatus(`Status: ${status}...`),
                        onComplete: handleComplete,
                        onFailure: handleFailure,
                    });
                } catch (jobError) {
                    handleFailure(jobError);
                }
            };
            runJob();
        } else {
            setJobStatus('No project is waiting in the editor.');
            setIsWorking(false);
        }

        return () => stopPolling?.();
    }, []);

    const audioUrl = buildMediaUrl(result?.audioUrl);
    const videoUrl = buildMediaUrl(result?.videoUrl);
    const transcriptUrl = buildMediaUrl(result?.transcriptUrl);
    const currentStage = getProcessingStage(jobStatus, Boolean(result));
    const progressPercent = result ? 100 : Math.max(8, Math.round((currentStage / processingSteps.length) * 100));

    const updateTranslatedSegment = (index, translated) => {
        setEditedSegments((segments) => segments.map((segment, segmentIndex) => (
            segmentIndex === index ? { ...segment, translated } : segment
        )));
    };

    const handleGenerateTts = async () => {
        if (!jobId || !editedSegments.length || isGeneratingTts) return;
        setIsGeneratingTts(true);
        setError('');
        setResult(null);
        setJobStatus('Creating a new voice track from your edited text...');
        try {
            const response = await fetch(`${API_BASE_URL}/api/jobs/${jobId}/generate-tts`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    translatedSegments: editedSegments,
                    outputFormat: draft?.selectedFormat || 'wav',
                    targetLanguage: draft?.selectedTarget || 'en',
                }),
            });
            const data = await response.json();
            if (!response.ok) throw new Error(formatError(data));

            startJobPolling(data.jobId, {
                onStatus: (status) => setJobStatus(`Updating your dubbed audio: ${status}...`),
                onComplete: (jobResult) => {
                    setResult(jobResult);
                    setEditedSegments(jobResult.translatedSegments || editedSegments);
                    setJobStatus('Your updated dub is ready.');
                    setIsGeneratingTts(false);
                },
                onFailure: (jobError) => {
                    setError(jobError instanceof Error ? jobError.message : 'Could not create the updated voice track.');
                    setJobStatus('The updated voice track could not be created.');
                    setIsGeneratingTts(false);
                },
            });
        } catch (generationError) {
            setError(generationError instanceof Error ? generationError.message : 'Could not create the updated voice track.');
            setJobStatus('The updated voice track could not be created.');
            setIsGeneratingTts(false);
        }
    };

    return (
        <main className="mx-auto max-w-5xl px-4 py-8 sm:px-6 lg:px-8">
            <Link href="/dubbing" className="inline-flex items-center gap-2 text-sm font-semibold text-slate-600 hover:text-slate-950">
                <ArrowLeft className="h-4 w-4" /> Back to setup
            </Link>

            <section className="mt-6 overflow-hidden rounded-[28px] bg-slate-950 text-white shadow-[0_24px_70px_-28px_rgba(15,23,42,0.6)]">
                <div className="border-b border-white/10 px-6 py-6 sm:px-10">
                    <p className="text-xs font-semibold uppercase tracking-[0.2em] text-indigo-300">Dubbing editor</p>
                    <div className="mt-3 flex flex-wrap items-start justify-between gap-4">
                        <div>
                            <h1 className="text-3xl font-semibold tracking-tight">{draft?.selectedFile?.name || 'Your dubbing project'}</h1>
                            <p className="mt-2 text-sm text-slate-400">
                                {draft ? `${draft.selectedSource.toUpperCase()} to ${draft.selectedTarget.toUpperCase()} · ${draft.selectedFormat.toUpperCase()}` : 'Live job workspace'}
                            </p>
                        </div>
                        <span className={`inline-flex items-center gap-2 rounded-full px-3 py-1.5 text-sm font-semibold ${error ? 'bg-red-400/15 text-red-200' : result ? 'bg-emerald-400/15 text-emerald-200' : 'bg-indigo-400/15 text-indigo-200'}`}>
                            {error ? <XCircle className="h-4 w-4" /> : result ? <CheckCircle2 className="h-4 w-4" /> : <LoaderCircle className="h-4 w-4 animate-spin" />}
                            {error ? 'Needs attention' : result ? 'Complete' : 'Working'}
                        </span>
                    </div>
                </div>

                <div className="px-6 py-8 sm:px-10 sm:py-12">
                    <div className="flex items-start gap-4">
                        <div className={`flex h-12 w-12 shrink-0 items-center justify-center rounded-2xl ${error ? 'bg-red-400/15 text-red-300' : result ? 'bg-emerald-400/15 text-emerald-300' : 'bg-indigo-400/15 text-indigo-300'}`}>
                            {error ? <XCircle className="h-6 w-6" /> : result ? <CheckCircle2 className="h-6 w-6" /> : <Sparkles className="h-6 w-6" />}
                        </div>
                        <div>
                            <h2 className="text-xl font-semibold">{jobStatus}</h2>
                            <p className="mt-2 max-w-2xl text-sm leading-6 text-slate-400">
                                {error || (result ? 'Your generated files are ready to review.' : 'This editor is handling the upload, transcription, translation, and voice generation.')}
                            </p>
                        </div>
                    </div>

                    {isWorking && <div className="mt-8 h-2 overflow-hidden rounded-full bg-white/10"><div className="h-full rounded-full bg-indigo-400 transition-all duration-700" style={{ width: `${progressPercent}%` }} /></div>}

                    <section className="mt-8 rounded-2xl border border-white/10 bg-white/[0.04] p-5 sm:p-6" aria-live="polite">
                        <div className="flex flex-wrap items-end justify-between gap-3">
                            <div>
                                <p className="text-xs font-semibold uppercase tracking-[0.18em] text-indigo-300">Your project journey</p>
                                <h2 className="mt-2 text-lg font-semibold text-white">We are taking care of each part</h2>
                            </div>
                            <p className="text-sm font-semibold text-slate-300">{progressPercent}% ready</p>
                        </div>
                        <div className="mt-4 h-2 overflow-hidden rounded-full bg-white/10">
                            <div className="h-full rounded-full bg-indigo-400 transition-all duration-700" style={{ width: `${progressPercent}%` }} />
                        </div>

                        <div className="mt-6 space-y-3">
                            {processingSteps.map((step, index) => {
                                const stepNumber = index + 1;
                                const isDone = stepNumber < currentStage || Boolean(result);
                                const isCurrent = !result && stepNumber === currentStage;
                                return (
                                    <div key={step.title} className={`flex gap-3 rounded-xl border p-4 transition ${isCurrent ? 'border-indigo-300/40 bg-indigo-400/10' : isDone ? 'border-emerald-300/10 bg-emerald-400/[0.04]' : 'border-white/5 bg-white/[0.02]'}`}>
                                        <div className={`flex h-8 w-8 shrink-0 items-center justify-center rounded-full text-sm font-bold ${isDone ? 'bg-emerald-400/20 text-emerald-300' : isCurrent ? 'bg-indigo-400 text-slate-950' : 'bg-white/10 text-slate-500'}`}>
                                            {isDone ? <CheckCircle2 className="h-4 w-4" /> : isCurrent ? <LoaderCircle className="h-4 w-4 animate-spin" /> : stepNumber}
                                        </div>
                                        <div className="min-w-0">
                                            <div className="flex flex-wrap items-center gap-2">
                                                <h3 className={`text-sm font-semibold ${isCurrent ? 'text-white' : isDone ? 'text-emerald-200' : 'text-slate-400'}`}>{step.title}</h3>
                                                {isCurrent && <span className="rounded-full bg-indigo-300/15 px-2 py-0.5 text-[11px] font-semibold text-indigo-200">In progress</span>}
                                                {isDone && !isCurrent && <span className="text-[11px] font-semibold text-emerald-300">Done</span>}
                                            </div>
                                            <p className="mt-1 text-sm leading-5 text-slate-400">{step.detail}</p>
                                        </div>
                                    </div>
                                );
                            })}
                        </div>
                    </section>

                    {editedSegments.length > 0 && (
                        <section className="mt-6 rounded-2xl border border-white/10 bg-white/[0.04] p-5 sm:p-6">
                            <div className="flex flex-wrap items-start justify-between gap-4">
                                <div>
                                    <p className="text-xs font-semibold uppercase tracking-[0.18em] text-indigo-300">Translation review</p>
                                    <h2 className="mt-2 text-lg font-semibold text-white">Shape the words before the final voice</h2>
                                    <p className="mt-2 max-w-2xl text-sm leading-6 text-slate-400">The translated lines are ready for your edits. Timestamps and original words stay locked so the new voice keeps the same timing.</p>
                                </div>
                                <span className="rounded-full bg-white/10 px-3 py-1.5 text-xs font-semibold text-slate-300">{editedSegments.length} timed lines</span>
                            </div>

                            <div className="mt-6 space-y-3">
                                {editedSegments.map((segment, index) => (
                                    <div key={`${segment.start}-${index}`} className="rounded-xl border border-white/10 bg-slate-950/40 p-4">
                                        <div className="flex flex-wrap items-center justify-between gap-2">
                                            <span className="text-xs font-semibold tabular-nums text-indigo-300">
                                                {formatTimestamp(segment.start)} - {formatTimestamp(segment.end)}
                                            </span>
                                            <span className="text-xs text-slate-500">Original words cannot be changed</span>
                                        </div>
                                        <p className="mt-3 rounded-lg bg-white/[0.04] px-3 py-2 text-sm leading-5 text-slate-400">{segment.text || 'No original text available.'}</p>
                                        <label className="mt-3 block">
                                            <span className="mb-2 block text-xs font-semibold uppercase tracking-[0.14em] text-emerald-300">Translated text</span>
                                            <textarea
                                                value={segment.translated || ''}
                                                onChange={(event) => updateTranslatedSegment(index, event.target.value)}
                                                rows={2}
                                                className="w-full resize-y rounded-lg border border-emerald-300/20 bg-slate-900 px-3 py-2.5 text-sm leading-6 text-white placeholder:text-slate-600 focus:border-emerald-300 focus:outline-none focus:ring-2 focus:ring-emerald-300/20"
                                            />
                                        </label>
                                    </div>
                                ))}
                            </div>

                            <div className="mt-6 flex flex-wrap items-center justify-between gap-4 border-t border-white/10 pt-5">
                                <p className="text-sm text-slate-400">Your edited lines will be used to create the new voice track.</p>
                                <button
                                    type="button"
                                    onClick={handleGenerateTts}
                                    disabled={isGeneratingTts || isWorking}
                                    className="inline-flex items-center gap-2 rounded-xl bg-emerald-400 px-4 py-3 text-sm font-bold text-slate-950 transition hover:bg-emerald-300 disabled:cursor-not-allowed disabled:opacity-50"
                                >
                                    {isGeneratingTts && <LoaderCircle className="h-4 w-4 animate-spin" />}
                                    {isGeneratingTts ? 'Generating new voice...' : 'Generate TTS from edited text'}
                                </button>
                            </div>
                        </section>
                    )}

                    {result && (
                        <div className="mt-8 grid gap-3 sm:grid-cols-3">
                            {audioUrl && <a href={audioUrl} target="_blank" rel="noreferrer" className="flex items-center gap-3 rounded-xl bg-white px-4 py-3 text-sm font-semibold text-slate-900 hover:bg-indigo-50"><FileAudio2 className="h-5 w-5 text-indigo-600" /> Download audio <Download className="ml-auto h-4 w-4" /></a>}
                            {videoUrl && <a href={videoUrl} target="_blank" rel="noreferrer" className="flex items-center gap-3 rounded-xl bg-white px-4 py-3 text-sm font-semibold text-slate-900 hover:bg-indigo-50"><FileVideo2 className="h-5 w-5 text-indigo-600" /> Download video <Download className="ml-auto h-4 w-4" /></a>}
                            {transcriptUrl && <a href={transcriptUrl} target="_blank" rel="noreferrer" className="flex items-center gap-3 rounded-xl bg-white px-4 py-3 text-sm font-semibold text-slate-900 hover:bg-indigo-50"><Download className="h-5 w-5 text-indigo-600" /> Download transcript <Download className="ml-auto h-4 w-4" /></a>}
                        </div>
                    )}
                </div>
            </section>
        </main>
    );
}
