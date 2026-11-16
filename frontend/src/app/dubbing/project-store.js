let activeDraft = null;
const DASHBOARD_JOBS_STORAGE_KEY = 'ai-dubbing-dashboard-jobs';

function readDashboardJobs() {
    if (typeof window === 'undefined') return [];
    try {
        const savedJobs = window.localStorage.getItem(DASHBOARD_JOBS_STORAGE_KEY);
        const jobs = savedJobs ? JSON.parse(savedJobs) : [];
        return Array.isArray(jobs) ? jobs : [];
    } catch {
        return [];
    }
}

function writeDashboardJobs(jobs) {
    window.localStorage.setItem(DASHBOARD_JOBS_STORAGE_KEY, JSON.stringify(jobs));
}

export function setDubbingDraft(draft) {
    activeDraft = draft;
}

export function getDubbingDraft() {
    return activeDraft;
}

export function clearDubbingDraft() {
    activeDraft = null;
}

export function upsertDashboardJob(job) {
    if (typeof window === 'undefined') return;
    const jobs = readDashboardJobs();
    const existingIndex = jobs.findIndex((item) => item.id === job.id);
    if (existingIndex === -1) {
        writeDashboardJobs([job, ...jobs]);
        return;
    }
    const updatedJobs = [...jobs];
    updatedJobs[existingIndex] = { ...updatedJobs[existingIndex], ...job };
    writeDashboardJobs(updatedJobs);
}

export function getDashboardJobs() {
    return readDashboardJobs();
}
