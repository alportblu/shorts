document.addEventListener("DOMContentLoaded", function() {
    const form = document.getElementById("videoForm");
    const loader = document.getElementById("loader");
    const loaderText = document.getElementById("loaderText");
    const progressBar = document.getElementById("progressBar");
    const thumbnailContainer = document.getElementById("thumbnail-container");
    const thumbnailImage = document.getElementById("thumbnail");
    const youtubeUrlInput = document.getElementById("youtube_url");
    const shortsContainer = document.getElementById("shortsContainer");
    const shortsList = document.getElementById("shortsList");

    youtubeUrlInput.addEventListener("input", function() {
        const videoUrl = youtubeUrlInput.value;
        const videoId = getYouTubeVideoId(videoUrl);

        if (videoId) {
            const thumbnailUrl = `https://img.youtube.com/vi/${videoId}/hqdefault.jpg`;
            thumbnailImage.src = thumbnailUrl;
            thumbnailContainer.style.display = "block";
        } else {
            thumbnailContainer.style.display = "none";
        }
    });

    let isProcessing = false;  // Flag para controlar submissões

    function startProcessing(event) {
        event.preventDefault();
        
        // Evitar múltiplas submissões
        if (isProcessing) {
            console.log('Already processing, ignoring click');
            return;
        }
        
        isProcessing = true;
        const form = document.getElementById('videoForm');
        const formData = new FormData(form);
        
        // Desabilitar o botão
        document.getElementById('submitBtn').disabled = true;
        
        // Esconder o formulário e mostrar o loader
        document.getElementById('videoForm').style.display = 'none';
        document.getElementById('loader').style.display = 'block';
        document.getElementById('error').style.display = 'none';
        
        fetch('/process', {
            method: 'POST',
            body: formData
        })
        .then(response => response.json())
        .then(data => {
            if (data.error) throw new Error(data.error);
            processId = data.process_id;
            // Iniciar checagem imediata
            checkStatus();
            // Configurar intervalo para checagens subsequentes
            statusCheckInterval = setInterval(checkStatus, 1000);
        })
        .catch(error => {
            // Em caso de erro, mostrar o formulário novamente
            document.getElementById('videoForm').style.display = 'block';
            document.getElementById('loader').style.display = 'none';
            showError(error.message);
            resetProcessing();
        });
    }

    function resetProcessing() {
        isProcessing = false;
        document.getElementById('submitBtn').disabled = false;
        if (statusCheckInterval) {
            clearInterval(statusCheckInterval);
            statusCheckInterval = null;
        }
    }

    function checkStatus() {
        if (!processId) {
            console.debug('No process ID available');
            return;
        }
        
        fetch(`/status/${processId}`)
            .then(response => {
                if (!response.ok) {
                    if (response.status === 404) {
                        resetProcessing();
                        return Promise.resolve(null);
                    }
                    throw new Error(response.status === 404 ? 'Processo não encontrado' : 'Erro ao verificar status');
                }
                return response.json();
            })
            .then(data => {
                if (!data) return;
                
                if (data.error) {
                    throw new Error(data.error);
                }
                
                // Manter o loader visível e atualizar o progresso
                document.getElementById('loader').style.display = 'block';
                document.getElementById('videoForm').style.display = 'none';
                document.getElementById('loaderText').textContent = data.step;
                document.getElementById('progressBar').value = data.progress;
                
                if (data.step === "Process completed") {
                    if (data.shorts_paths && data.shorts_paths.length > 0) {
                        showShortsModal(data.shorts_paths);
                    }
                    resetProcessing();
                    // Restaurar interface apenas após completar
                    document.getElementById('videoForm').style.display = 'block';
                    document.getElementById('loader').style.display = 'none';
                }
                
                if (data.step === "Error") {
                    resetProcessing();
                    document.getElementById('videoForm').style.display = 'block';
                    document.getElementById('loader').style.display = 'none';
                    showError(data.error || 'Erro ao processar vídeo');
                }
            })
            .catch(error => {
                // Lista de erros para ignorar
                const ignoredErrors = [
                    'Failed to check status',
                    'Failed to fetch',
                    'Process not found',
                    'status/undefined'
                ];
                
                if (ignoredErrors.some(err => error.message.toLowerCase().includes(err.toLowerCase()))) {
                    return;
                }
                
                console.error('Status check error:', error);
                resetProcessing();
                document.getElementById('videoForm').style.display = 'block';
                document.getElementById('loader').style.display = 'none';
                showError(error.message);
            });
    }

    function getYouTubeVideoId(url) {
        const regExp = /^.*(youtu\.be\/|v\/|u\/\w\/|embed\/|watch\?v=|\&v=)([^#\&\?]*).*/;
        const match = url.match(regExp);
        return (match && match[2].length == 11) ? match[2] : null;
    }

    function resetStatus() {
        fetch('/reset', {
            method: 'POST'
        })
        .then(response => response.json())
        .then(data => {
            clearError();
            enableForm();
        })
        .catch(error => console.error('Error:', error));
    }

    function clearError() {
        const errorDiv = document.getElementById('error');
        if (errorDiv) {
            errorDiv.style.display = 'none';
        }
    }

    function updateShortsList(shortsPaths) {
        shortsList.innerHTML = "";
        shortsPaths.forEach(shortPath => {
            const listItem = document.createElement("li");
            const link = document.createElement("a");
            link.href = `/shorts/${shortPath.split('/').pop()}`;
            link.innerText = `Download ${shortPath.split('/').pop()}`;
            link.download = true;
            listItem.appendChild(link);
            shortsList.appendChild(listItem);
        });
    }

    function enableForm() {
        loader.style.display = "none";
        form.style.display = "block";
    }

    function showError(message) {
        const errorDiv = document.getElementById('error') || createErrorDiv();
        errorDiv.textContent = message;
        errorDiv.style.display = 'block';
    }

    function createErrorDiv() {
        const errorDiv = document.createElement('div');
        errorDiv.id = 'error';
        errorDiv.className = 'error';
        form.parentNode.insertBefore(errorDiv, form);
        return errorDiv;
    }

    function updateProgress(data) {
        progressBar.value = data.progress;
        
        // Mensagens mais detalhadas e progresso mais realista
        const messages = {
            'Idle': 'Ready to process your video...',
            'Downloading video...': 'Getting your video ready... ⬇️ (10%)',
            'Extracting audio...': 'Analyzing the audio... 🎵 (20%)',
            'Generating transcript...': 'Understanding what\'s being said... 📝 (30%)',
            'Identifying highlights...': 'Finding the best moments... ✨ (40%)',
            'Cutting video into shorts...': {
                start: 'Starting to create your shorts... ✂️',
                processing: (current, total) => 
                    `Creating short ${current}/${total}... (${Math.round(40 + (current/total * 50))}%)`,
                subtitles: (current, total) => 
                    `Adding subtitles to short ${current}/${total}...`,
                finalizing: 'Finalizing your shorts...'
            },
            'Process completed': 'All done! Your shorts are ready! 🎉'
        };
        
        // Atualizar mensagem baseado no estado atual
        if (data.step === 'Cutting video into shorts...') {
            if (data.currentShort && data.totalShorts) {
                loaderText.textContent = messages[data.step].processing(
                    data.currentShort, 
                    data.totalShorts
                );
            } else {
                loaderText.textContent = messages[data.step].start;
            }
        } else {
            loaderText.textContent = messages[data.step] || data.step;
        }
    }

    function showSuccess(message) {
        const successDiv = document.createElement('div');
        successDiv.className = 'success';
        successDiv.textContent = '🎉 ' + message;
        form.parentNode.insertBefore(successDiv, shortsContainer);
        
        // Remover após 5 segundos
        setTimeout(() => successDiv.remove(), 5000);
    }

    function stopPolling() {
        loader.style.display = "none";
        if (shortsContainer) {
            shortsContainer.style.display = "block";
        }
    }

    function saveVideo(videoPath, title) {
        fetch('/save-video', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/x-www-form-urlencoded',
            },
            body: `video_path=${encodeURIComponent(videoPath)}&title=${encodeURIComponent(title)}`
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                showSuccess('Video saved successfully!');
            } else {
                showError('Failed to save video');
            }
        })
        .catch(error => {
            console.error('Error:', error);
            showError('Failed to save video');
        });
    }

    function showShortsModal(shorts) {
        const container = document.getElementById('shortsContainer');
        const list = document.getElementById('shortsList');
        list.innerHTML = '';
        
        shorts.forEach(short => {
            const item = document.createElement('div');
            item.className = 'short-item';
            item.innerHTML = `
                <video controls>
                    <source src="/shorts/${short}" type="video/mp4">
                </video>
                <div class="short-actions">
                    <a href="/shorts/${short}" download class="download-btn">Download</a>
                    <button onclick="saveVideo('/shorts/${short}', '${short}')" class="save-btn">
                        Save for Later
                    </button>
                </div>
            `;
            list.appendChild(item);
        });
        
        container.style.display = 'block';
    }

    // Adicionar event listener ao form
    document.getElementById('videoForm').addEventListener('submit', startProcessing);
});
