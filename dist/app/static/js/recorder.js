document.addEventListener('DOMContentLoaded', function() {
    const videoPreview = document.getElementById('video-preview');
    const startButton = document.getElementById('start-button');
    const stopButton = document.getElementById('stop-button');
    const switchCameraButton = document.getElementById('switch-camera-button');
    const status = document.getElementById('status');
    const uploadForm = document.getElementById('upload-form');

    if (!videoPreview) return;

    let mediaRecorder;
    let recordedChunks = [];
    let stream;
    let currentFacingMode = 'user'; // 'user' - фронтальная, 'environment' - тыловая
    let videoDevices = [];
    let currentDeviceIndex = 0;

    async function getDevices() {
        try {
            const devices = await navigator.mediaDevices.enumerateDevices();
            videoDevices = devices.filter(device => device.kind === 'videoinput');
            if (videoDevices.length > 1) {
                switchCameraButton.classList.remove('hidden');
            }
        } catch (error) {
            console.error('Ошибка получения списка устройств:', error);
        }
    }

    async function setupStream() {
        if (stream) {
            stream.getTracks().forEach(track => track.stop());
        }

        const constraints = {
            video: {
                deviceId: videoDevices.length > 0 ? { exact: videoDevices[currentDeviceIndex].deviceId } : undefined
            },
            audio: true
        };

        try {
            stream = await navigator.mediaDevices.getUserMedia(constraints);
            videoPreview.srcObject = stream;
            status.textContent = 'Камера готова. Нажмите "Начать запись".';
            if (videoDevices.length === 0) {
                await getDevices();
            }
        } catch (error) {
            console.error('Ошибка доступа к камере:', error);
            status.textContent = 'Ошибка: Не удалось получить доступ к камере. Пожалуйста, разрешите доступ в настройках браузера.';
            startButton.disabled = true;
            switchCameraButton.classList.add('hidden');
        }
    }

    setupStream();

    switchCameraButton.addEventListener('click', () => {
        if (videoDevices.length > 1) {
            currentDeviceIndex = (currentDeviceIndex + 1) % videoDevices.length;
            setupStream();
        }
    });

    startButton.addEventListener('click', () => {
        if (!stream) {
            status.textContent = 'Камера не готова.';
            return;
        }
        recordedChunks = [];
        mediaRecorder = new MediaRecorder(stream, { mimeType: 'video/webm' });

        mediaRecorder.ondataavailable = (event) => {
            if (event.data.size > 0) {
                recordedChunks.push(event.data);
            }
        };

        mediaRecorder.onstop = () => {
            const videoBlob = new Blob(recordedChunks, { type: 'video/webm' });
            const videoFile = new File([videoBlob], 'recorded-video.webm', { type: 'video/webm' });
            const dataTransfer = new DataTransfer();
            dataTransfer.items.add(videoFile);

            let fileInput = uploadForm.querySelector('input[name="media_file"]');
            if (!fileInput) {
                fileInput = document.createElement('input');
                fileInput.type = 'file';
                fileInput.name = 'media_file';
                fileInput.style.display = 'none';
                uploadForm.appendChild(fileInput);
            }
            fileInput.files = dataTransfer.files;

            uploadForm.classList.remove('hidden');
            document.getElementById('controls').classList.add('hidden');
            status.textContent = 'Запись завершена. Заполните детали и отправьте отзыв.';
            
            stream.getTracks().forEach(track => track.stop());

            videoPreview.srcObject = null;
            videoPreview.src = URL.createObjectURL(videoBlob);
            videoPreview.muted = false;
            videoPreview.controls = true;
        };
        
        mediaRecorder.start();
        startButton.classList.add('hidden');
        stopButton.classList.remove('hidden');
        switchCameraButton.classList.add('hidden'); // Скрываем смену камеры во время записи
        status.textContent = 'Идёт запись...';
    });

    stopButton.addEventListener('click', () => {
        if (mediaRecorder && mediaRecorder.state === 'recording') {
            mediaRecorder.stop();
        }
    });
});