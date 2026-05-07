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

    function startDubbing() {
        // Show progress section
        form.style.display = 'none';
        progressSection.style.display = 'block';

        // Disable start button
        startBtn.disabled = true;
        startBtn.textContent = 'Processing...';

        // Simulate progress (in real implementation, this would connect to backend)
        simulateProgress();
    }

    function simulateProgress() {
        const steps = [
            '🎬 Initializing pipeline...',
            '🔊 Audio enhancement...',
            '🎤 Transcribing audio...',
            '🌍 Translating text...',
            '🎙️ Generating speech...',
            '🎬 Processing video...',
            '✅ Finalizing...'
        ];

        let currentStep = 0;
        const totalSteps = steps.length;

        const interval = setInterval(() => {
            if (currentStep < totalSteps) {
                const progress = ((currentStep + 1) / totalSteps) * 100;
                progressFill.style.width = progress + '%';
                progressText.textContent = steps[currentStep];

                // Add to log
                logOutput.textContent += `[${new Date().toLocaleTimeString()}] ${steps[currentStep]}\n`;
                logOutput.scrollTop = logOutput.scrollHeight;

                currentStep++;
            } else {
                clearInterval(interval);
                showResults();
            }
        }, 2000); // 2 seconds per step
    }

    function showResults() {
        progressSection.style.display = 'none';
        resultsSection.style.display = 'block';

        // In a real implementation, these would be actual file URLs from the backend
        // For demo purposes, we'll show placeholder content
        const audioPlayer = document.getElementById('audioPlayer');
        const videoPlayer = document.getElementById('videoPlayer');
        const videoResult = document.getElementById('videoResult');

        // Check if input was video
        const inputFile = fileInput.files[0];
        const isVideo = inputFile.type.startsWith('video/');

        if (isVideo) {
            videoResult.style.display = 'block';
            // videoPlayer.src = 'path/to/dubbed/video.mp4';
            // document.getElementById('videoDownload').href = 'path/to/dubbed/video.mp4';
        } else {
            videoResult.style.display = 'none';
        }

        // audioPlayer.src = 'path/to/dubbed/audio.wav';
        // document.getElementById('audioDownload').href = 'path/to/dubbed/audio.wav';
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