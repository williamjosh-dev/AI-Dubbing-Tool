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

export default function DubbingEditorPage() {
    const [draft, setDraft] = useState(null);
    const [jobStatus, setJobStatus] = useState('Preparing your editor...');
    const [result, setResult] = useState(null);
    const [error, setError] = useState('');
    const [isWorking, setIsWorking] = useState(true);

    useEffect(() => {
        let stopPolling;
        const activeJob = window.localStorage.getItem(ACTIVE_JOB_STORAGE_KEY);
        const savedDraft = getDubbingDraft();

        if (savedDraft) setDraft(savedDraft);

        const handleComplete = (jobResult) => {
            setResult(jobResult);
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
            stopPolling = startJobPolling(JSON.parse(activeJob).jobId, {
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

                    {isWorking && <div className="mt-8 h-2 overflow-hidden rounded-full bg-white/10"><div className="h-full w-2/5 animate-pulse rounded-full bg-indigo-400" /></div>}

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
