document.addEventListener('DOMContentLoaded', function () {
    const uploadForm = document.getElementById('upload-form');
    const fileInput = document.getElementById('file-input');
    const fileListContainer = document.getElementById('file-list');
    const submitButton = document.getElementById('submit-button');
    const progressContainer = document.getElementById('progress-container');
    const progressBar = document.getElementById('progress-bar');
    const progressText = document.getElementById('progress-text');
    const errorMessage = document.getElementById('error-message');

    let selectedFiles = [];

    fileInput.addEventListener('change', () => {
        selectedFiles = Array.from(fileInput.files);
        updateFileList();
    });

    function updateFileList() {
        fileListContainer.innerHTML = '';
        selectedFiles.forEach((file, index) => {
            const fileElement = document.createElement('div');
            fileElement.className = 'flex items-center justify-between bg-slate-700/50 p-2 rounded';
            fileElement.innerHTML = `
                <span class="text-sm text-gray-300 truncate">${file.name}</span>
                <button type="button" data-index="${index}" class="remove-file-btn text-red-400 hover:text-red-600">&times;</button>
            `;
            fileListContainer.appendChild(fileElement);
        });
    }

    fileListContainer.addEventListener('click', (e) => {
        if (e.target.classList.contains('remove-file-btn')) {
            const indexToRemove = parseInt(e.target.dataset.index, 10);
            selectedFiles.splice(indexToRemove, 1);
            
            // Create a new FileList and assign it back to the input
            const dataTransfer = new DataTransfer();
            selectedFiles.forEach(file => dataTransfer.items.add(file));
            fileInput.files = dataTransfer.files;

            updateFileList();
        }
    });

    uploadForm.addEventListener('submit', async function (event) {
        event.preventDefault();
        
        if (selectedFiles.length === 0) {
            showError('Please select at least one file.');
            return;
        }

        submitButton.disabled = true;
        submitButton.textContent = 'Uploading...';
        progressContainer.classList.remove('hidden');
        progressText.textContent = '';
        hideError();

        const uploadPromises = selectedFiles.map(file => {
            if (file.size > 50 * 1024 * 1024) { // 50 MB
                return Promise.reject(`File ${file.name} is too large.`);
            }
            return uploadFile(file);
        });

        try {
            const objectNames = await Promise.all(uploadPromises);

            progressText.textContent = "Finalizing...";

            const formData = new FormData(uploadForm);
            const reviewData = {
                what: formData.get('what'),
                where: formData.get('where'),
                title: formData.get('title'),
                description: formData.get('description'),
                category: formData.get('category'),
                rating: formData.get('rating'),
                objectNames: objectNames, // Отправляем массив имен
            };

            const response = await fetch('/upload', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(reviewData)
            });

            const result = await response.json();

            if (response.ok && result.redirectUrl) {
                window.location.href = result.redirectUrl;
            } else {
                throw new Error(result.message || 'Failed to save review details.');
            }

        } catch (error) {
            showError(error.message || 'An unexpected error occurred.');
            resetUploadUI();
        }
    });

    async function uploadFile(file) {
        // Получаем presigned URL
        const presignedUrlResponse = await fetch('/api/generate-upload-url', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ filename: file.name, contentType: file.type })
        });
        if (!presignedUrlResponse.ok) {
            throw new Error('Could not get upload URL.');
        }
        const { url, objectName } = await presignedUrlResponse.json();

        // Загружаем файл в R2
        const uploadResponse = await fetch(url, {
            method: 'PUT',
            body: file,
            headers: { 'Content-Type': file.type }
        });
        if (!uploadResponse.ok) {
            throw new Error(`Failed to upload ${file.name}.`);
        }
        
        // Обновляем общий прогресс (упрощенно)
        updateOverallProgress(selectedFiles.length);

        return {
            objectName: objectName,
            mediaType: file.type.startsWith('image/') ? 'image' : 'video'
        };
    }
    
    let completedUploads = 0;
    function updateOverallProgress(totalFiles) {
        completedUploads++;
        const progress = (completedUploads / totalFiles) * 100;
        progressBar.style.width = `${progress}%`;
        progressText.textContent = `Uploaded ${completedUploads} of ${totalFiles} files.`;
    }

    function showError(message) {
        errorMessage.textContent = message;
        errorMessage.classList.remove('hidden');
    }

    function hideError() {
        errorMessage.classList.add('hidden');
    }
    
    function resetUploadUI() {
        submitButton.disabled = false;
        submitButton.textContent = 'Submit Review';
        progressContainer.classList.add('hidden');
        progressBar.style.width = '0%';
        progressText.textContent = '';
        completedUploads = 0;
    }
});