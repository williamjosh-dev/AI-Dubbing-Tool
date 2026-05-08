// Advanced JavaScript for AI Dubbing Studio
window.addEventListener('DOMContentLoaded', () => {
    const form = document.getElementById('dubbingForm');
    const fileInput = document.getElementById('audioFile');
    const fileInfo = document.getElementById('fileInfo');
    const fileName = document.getElementById('fileName');
    const fileSize = document.getElementById('fileSize');
    const voiceClone = document.getElementById('voiceClone');
    const voiceMethod = document.getElementById('voiceMethod');
    const startBtn = document.getElementById('startBtn');
    const resetBtn = document.getElementById('resetBtn');
    const progressSection = document.getElementById('progressSection');
    const progressFill = document.getElementById('progressFill');

    voiceMethod.disabled = true;
    voiceMethod.parentElement.style.opacity = '0.65';
    const progressPercent = document.getElementById('progressPercent');
    const progressText = document.getElementById('progressText');
    const logOutput = document.getElementById('logOutput');
    const resultsSection = document.getElementById('resultsSection');
    const videoResult = document.getElementById('videoResult');
    const translatedText = document.getElementById('translatedText');
    const resultDetails = document.getElementById('resultDetails');
    const dropzone = document.getElementById('dropzone');

    const audioPlayer = document.getElementById('audioPlayer');
    const audioDownload = document.getElementById('audioDownload');
    const videoPlayer = document.getElementById('videoPlayer');
    const videoDownload = document.getElementById('videoDownload');

    fileInput.addEventListener('change', ({ target }) => {
        const file = target.files[0];
        if (file) {
            fileName.textContent = file.name;
            fileSize.textContent = formatFileSize(file.size);
            fileInfo.hidden = false;
        } else {
            fileInfo.hidden = true;
        }
    });

    voiceClone.addEventListener('change', () => {
        const voiceMethod = document.getElementById('voiceMethod');
        voiceMethod.disabled = !voiceClone.checked;
        voiceMethod.parentElement.style.opacity = voiceClone.checked ? '1' : '0.65';
    });

    form.addEventListener('submit', async (event) => {
        event.preventDefault();
        if (!fileInput.files[0]) {
            window.alert('Select a valid audio or video file first.');
            return;
        }
        await startDubbing();
    });

    resetBtn.addEventListener('click', resetForm);

    ['dragenter', 'dragover', 'dragleave', 'drop'].forEach((eventName) => {
        dropzone.addEventListener(eventName, preventDefaults, false);
    });

    ['dragenter', 'dragover'].forEach((eventName) => {
        dropzone.addEventListener(eventName, () => dropzone.classList.add('dragover'), false);
    });

    ['dragleave', 'drop'].forEach((eventName) => {
        dropzone.addEventListener(eventName, () => dropzone.classList.remove('dragover'), false);
    });

    dropzone.addEventListener('drop', handleDrop, false);

    function preventDefaults(event) {
        event.preventDefault();
        event.stopPropagation();
    }

    function handleDrop(event) {
        const files = event.dataTransfer.files;
        if (files.length > 0) {
            fileInput.files = files;
            fileInput.dispatchEvent(new Event('change'));
        }
    }

    async function startDubbing() {
        form.querySelectorAll('button').forEach((button) => button.setAttribute('disabled', 'true'));
        resultsSection.hidden = true;
        progressSection.hidden = false;
        updateProgress(10, 'Uploading file to server...');
        logOutput.textContent = 'Uploading source file...\n';

        const requestData = new FormData(form);

        try {
            const response = await fetch('/api/dub', {
                method: 'POST',
                body: requestData,
            });

            if (!response.ok) {
                const errorPayload = await response.json().catch(() => null);
                throw new Error(errorPayload?.error || 'Server failed to process the request.');
            }

            updateProgress(40, 'Server is processing transcription and translation...');
            logOutput.textContent += 'Server accepted file. Processing pipeline...\n';

            const result = await response.json();

            updateProgress(85, 'Finalizing generated output...');
            logOutput.textContent += 'Pipeline completed. Preparing results...\n';

            renderResults(result);
            updateProgress(100, 'Complete!');
        } catch (error) {
            updateProgress(100, 'Error occurred');
            logOutput.textContent += `Error: ${error.message}\n`;
            window.alert(error.message);
            progressSection.hidden = true;
        } finally {
            form.querySelectorAll('button').forEach((button) => button.removeAttribute('disabled'));
        }
    }

    function renderResults(result) {
        progressSection.hidden = true;
        resultsSection.hidden = false;

        audioPlayer.src = result.audioUrl;
        audioDownload.href = result.audioUrl;

        translatedText.textContent = result.translatedText || 'No translated transcript available.';

        if (result.videoUrl) {
            videoResult.hidden = false;
            videoPlayer.src = result.videoUrl;
            videoDownload.href = result.videoUrl;
        } else {
            videoResult.hidden = true;
            videoPlayer.src = '';
        }

        const details = [
            { label: 'Source file', value: result.sourceFile || 'Unknown' },
            { label: 'Source language', value: result.sourceLang || 'auto' },
            { label: 'Target language', value: result.targetLang || 'auto' },
            { label: 'TTS engine', value: result.voiceMethod || 'Auto' },
            { label: 'Voice cloning', value: result.voiceClone ? 'Enabled' : 'Disabled' },
            { label: 'Audio enhancement', value: result.enhanceAudio ? 'Enabled' : 'Disabled' },
            { label: 'Video output', value: result.videoUrl ? 'Generated' : 'Audio only' },
        ];

        resultDetails.innerHTML = details.map((item) => `
            <div class="meta-item">
                <strong>${item.label}</strong>
                <span>${item.value}</span>
            </div>
        `).join('');
    }

    function updateProgress(value, label) {
        progressFill.style.width = `${value}%`;
        progressPercent.textContent = `${value}%`;
        progressText.textContent = label;
    }

    function resetForm() {
        form.reset();
        fileInfo.hidden = true;
        resultsSection.hidden = true;
        progressSection.hidden = true;
        progressFill.style.width = '0%';
        progressPercent.textContent = '0%';
        progressText.textContent = 'Waiting for upload...';
        logOutput.textContent = '';
        audioPlayer.src = '';
        videoPlayer.src = '';
    }

    function formatFileSize(bytes) {
        if (!bytes) return '0 Bytes';
        const units = ['Bytes', 'KB', 'MB', 'GB'];
        const index = Math.floor(Math.log(bytes) / Math.log(1024));
        return `${(bytes / Math.pow(1024, index)).toFixed(2)} ${units[index]}`;
    }
});
