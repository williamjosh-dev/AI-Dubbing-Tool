let activeDraft = null;

export function setDubbingDraft(draft) {
    activeDraft = draft;
}

export function getDubbingDraft() {
    return activeDraft;
}

export function clearDubbingDraft() {
    activeDraft = null;
}
