// Simple JavaScript for Dubbing MVP UI
document.addEventListener('DOMContentLoaded', function() {
    // DOM elements
    const form = document.getElementById('dubbingForm');
    const fileInput = document.getElementById('audioFile');
    const fileInfo = document.getElementById('fileInfo');
    const fileName = document.getElementById('fileName');
    const fileSize = document.getElementById('fileSize');
    const voiceClone = document.getElementById('voiceClone');
    const voiceOptions = document.getElementById('voiceOptions');
    const startBtn = document.getElementById('startBtn');
    const resetBtn = document.getElementById('resetBtn');
    const progressSection = document.getElementById('progressSection');
    const progressFill = document.getElementById('progressFill');
    const progressText = document.getElementById('progressText');
    const logOutput = document.getElementById('logOutput');
    const resultsSection = document.getElementById('resultsSection');

    // File upload handling
    fileInput.addEventListener('change', function(e) {
        const file = e.target.files[0];
        if (file) {
            fileName.textContent = file.name;
            fileSize.textContent = formatFileSize(file.size);
            fileInfo.style.display = 'block';
        } else {
            fileInfo.style.display = 'none';
        }
    });

    // Voice clone options toggle
    voiceClone.addEventListener('change', function() {
        voiceOptions.style.display = this.checked ? 'block' : 'none';
    });

    // Form submission
    form.addEventListener('submit', function(e) {
        e.preventDefault();

        if (!fileInput.files[0]) {
            alert('Please select a file to dub.');
            return;
        }

        startDubbing();
    });

    // Reset button
    resetBtn.addEventListener('click', resetForm);

    async function startDubbing() {
        form.style.display = 'none';
        progressSection.style.display = 'block';
        startBtn.disabled = true;
        startBtn.textContent = 'Processing...';
        progressFill.style.width = '10%';
        progressText.textContent = 'Uploading file...';
        logOutput.textContent = '';

        const requestData = new FormData(form);

        try {
            const response = await fetch('/api/dub', {
                method: 'POST',
                body: requestData,
            });

            if (!response.ok) {
                const errorData = await response.json().catch(() => null);
                throw new Error(errorData?.error || 'Server error while dubbing audio.');
            }

            progressFill.style.width = '60%';
            progressText.textContent = 'Processing audio on server...';
            logOutput.textContent += `[${new Date().toLocaleTimeString()}] Upload complete, waiting for server response...\n`;

            const result = await response.json();
            progressFill.style.width = '100%';
            progressText.textContent = 'Finalizing output...';
            logOutput.textContent += `[${new Date().toLocaleTimeString()}] Processing complete.\n`;

            showResults(result);
        } catch (error) {
            progressText.textContent = 'Error';
            progressFill.style.width = '100%';
            logOutput.textContent += `[${new Date().toLocaleTimeString()}] ${error.message}\n`;
            alert(error.message);
            startBtn.disabled = false;
            startBtn.textContent = '🚀 Start Dubbing';
            form.style.display = 'block';
            progressSection.style.display = 'none';
        }
    }

    function showResults(result) {
        progressSection.style.display = 'none';
        resultsSection.style.display = 'block';

        const audioPlayer = document.getElementById('audioPlayer');
        const audioDownload = document.getElementById('audioDownload');
        const translatedText = document.getElementById('translatedText');
        const videoResult = document.getElementById('videoResult');
        const videoPlayer = document.getElementById('videoPlayer');
        const videoDownload = document.getElementById('videoDownload');

        audioPlayer.src = result.audioUrl;
        audioDownload.href = result.audioUrl;

        translatedText.textContent = result.translatedText || 'No translated text available.';

        if (result.isVideo && result.videoUrl) {
            videoResult.style.display = 'block';
            videoPlayer.src = result.videoUrl;
            videoDownload.href = result.videoUrl;
        } else {
            videoResult.style.display = 'none';
        }
    }

    function resetForm() {
        form.reset();
        form.style.display = 'block';
        progressSection.style.display = 'none';
        resultsSection.style.display = 'none';
        fileInfo.style.display = 'none';
        voiceOptions.style.display = 'none';
        startBtn.disabled = false;
        startBtn.textContent = '🚀 Start Dubbing';
        progressFill.style.width = '0%';
        progressText.textContent = 'Initializing...';
        logOutput.textContent = '';
    }

    function formatFileSize(bytes) {
        if (bytes === 0) return '0 Bytes';
        const k = 1024;
        const sizes = ['Bytes', 'KB', 'MB', 'GB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
    }

    // Drag and drop functionality
    const uploadArea = document.querySelector('.upload-area');

    ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
        uploadArea.addEventListener(eventName, preventDefaults, false);
    });

    function preventDefaults(e) {
        e.preventDefault();
        e.stopPropagation();
    }

    ['dragenter', 'dragover'].forEach(eventName => {
        uploadArea.addEventListener(eventName, highlight, false);
    });

    ['dragleave', 'drop'].forEach(eventName => {
        uploadArea.addEventListener(eventName, unhighlight, false);
    });

    function highlight(e) {
        uploadArea.classList.add('highlight');
    }

    function unhighlight(e) {
        uploadArea.classList.remove('highlight');
    }

    uploadArea.addEventListener('drop', handleDrop, false);

    function handleDrop(e) {
        const dt = e.dataTransfer;
        const files = dt.files;

        if (files.length > 0) {
            fileInput.files = files;
            fileInput.dispatchEvent(new Event('change'));
        }
    }
});