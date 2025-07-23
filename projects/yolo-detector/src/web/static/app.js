// YOLO Object Detector Web Application

class YOLODetectorApp {
    constructor() {
        this.ws = null;
        this.isStreaming = false;
        this.isRawFeed = false;
        this.streamUrl = '/processed-stream';
        this.rawStreamUrl = '/stream';
        this.reconnectAttempts = 0;
        this.maxReconnectAttempts = 5;
        this.reconnectDelay = 3000;
        this.stats = {
            totalDetections: 0,
            avgFps: 0,
            fpsHistory: []
        };
        
        this.initializeElements();
        this.setupEventListeners();
        this.connectWebSocket();
        this.loadSettings();
    }

    initializeElements() {
        // Main elements
        this.statusIndicator = document.getElementById('status-indicator');
        this.videoFeed = document.getElementById('video-feed');
        this.videoContainer = document.getElementById('video-container');
        this.detectionsListElement = document.getElementById('detections-list');
        
        // Controls
        this.toggleStreamBtn = document.getElementById('toggle-stream');
        this.toggleRawBtn = document.getElementById('toggle-raw');
        this.fullscreenBtn = document.getElementById('fullscreen');
        
        // Stats
        this.fpsDisplay = document.getElementById('fps-display');
        this.detectionCount = document.getElementById('detection-count');
        this.totalDetections = document.getElementById('total-detections');
        this.avgFps = document.getElementById('avg-fps');
        
        // Status indicators
        this.cameraStatus = document.getElementById('camera-status');
        this.detectorStatus = document.getElementById('detector-status');
        this.trackingStatus = document.getElementById('tracking-status');
        this.segmentationStatus = document.getElementById('segmentation-status');
        
        // Settings
        this.confidenceThreshold = document.getElementById('confidence-threshold');
        this.confidenceValue = document.getElementById('confidence-value');
        this.iouThreshold = document.getElementById('iou-threshold');
        this.iouValue = document.getElementById('iou-value');
        this.enableTracking = document.getElementById('enable-tracking');
        this.enableSegmentation = document.getElementById('enable-segmentation');
        this.modelSelect = document.getElementById('model-select');
        this.cameraUrl = document.getElementById('camera-url');
        
        // Buttons
        this.applySettingsBtn = document.getElementById('apply-settings');
        this.testCameraBtn = document.getElementById('test-camera');
        
        // CLI
        this.cliOutput = document.getElementById('cli-output');
        this.cliInput = document.getElementById('cli-input');
        this.cliSend = document.getElementById('cli-send');
    }

    setupEventListeners() {
        // Stream controls
        this.toggleStreamBtn.addEventListener('click', () => this.toggleStream());
        this.toggleRawBtn.addEventListener('click', () => this.toggleRawFeed());
        this.fullscreenBtn.addEventListener('click', () => this.toggleFullscreen());
        
        // Settings
        this.confidenceThreshold.addEventListener('input', (e) => {
            this.confidenceValue.textContent = parseFloat(e.target.value).toFixed(2);
        });
        
        this.iouThreshold.addEventListener('input', (e) => {
            this.iouValue.textContent = parseFloat(e.target.value).toFixed(2);
        });
        
        this.applySettingsBtn.addEventListener('click', () => this.applySettings());
        this.testCameraBtn.addEventListener('click', () => this.testCamera());
        
        // CLI
        this.cliSend.addEventListener('click', () => this.sendCliCommand());
        this.cliInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') this.sendCliCommand();
        });
        
        // Class filters
        this.setupClassFilters();
        
        // Keyboard shortcuts
        document.addEventListener('keydown', (e) => this.handleKeyboard(e));
        
        // Fullscreen escape
        document.addEventListener('fullscreenchange', () => this.handleFullscreenChange());
    }

    setupClassFilters() {
        const selectAllBtn = document.getElementById('select-all-classes');
        const clearAllBtn = document.getElementById('clear-all-classes');
        
        selectAllBtn?.addEventListener('click', () => {
            const checkboxes = document.querySelectorAll('#class-filters input[type="checkbox"]');
            checkboxes.forEach(cb => cb.checked = true);
        });
        
        clearAllBtn?.addEventListener('click', () => {
            const checkboxes = document.querySelectorAll('#class-filters input[type="checkbox"]');
            checkboxes.forEach(cb => cb.checked = false);
        });
    }

    connectWebSocket() {
        const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
        const wsUrl = `${protocol}//${window.location.host}/ws`;
        
        this.updateStatus('connecting', 'Connecting...');
        
        try {
            this.ws = new WebSocket(wsUrl);
            
            this.ws.onopen = () => {
                console.log('WebSocket connected');
                this.updateStatus('connected', 'Connected');
                this.reconnectAttempts = 0;
                
                // Subscribe to detection updates
                this.sendWebSocketMessage({
                    type: 'subscribe',
                    subscription: 'detections'
                });
                
                // Subscribe to stats updates
                this.sendWebSocketMessage({
                    type: 'subscribe',
                    subscription: 'stats'
                });
            };
            
            this.ws.onmessage = (event) => {
                try {
                    const message = JSON.parse(event.data);
                    this.handleWebSocketMessage(message);
                } catch (error) {
                    console.error('WebSocket message parse error:', error);
                }
            };
            
            this.ws.onclose = () => {
                console.log('WebSocket disconnected');
                this.updateStatus('disconnected', 'Disconnected');
                this.scheduleReconnect();
            };
            
            this.ws.onerror = (error) => {
                console.error('WebSocket error:', error);
                this.updateStatus('disconnected', 'Connection Error');
            };
            
        } catch (error) {
            console.error('WebSocket connection error:', error);
            this.updateStatus('disconnected', 'Failed to Connect');
        }
    }

    scheduleReconnect() {
        if (this.reconnectAttempts < this.maxReconnectAttempts) {
            this.reconnectAttempts++;
            this.updateStatus('connecting', `Reconnecting... (${this.reconnectAttempts}/${this.maxReconnectAttempts})`);
            
            setTimeout(() => {
                this.connectWebSocket();
            }, this.reconnectDelay);
        } else {
            this.updateStatus('disconnected', 'Connection Failed');
        }
    }

    sendWebSocketMessage(message) {
        if (this.ws && this.ws.readyState === WebSocket.OPEN) {
            this.ws.send(JSON.stringify(message));
        }
    }

    handleWebSocketMessage(message) {
        switch (message.type) {
            case 'welcome':
                console.log('Welcome message received:', message);
                break;
                
            case 'detections':
                this.updateDetections(message.data);
                break;
                
            case 'stats':
                this.updateStats(message.data);
                break;
                
            case 'frame':
                if (message.image) {
                    this.videoFeed.src = message.image;
                }
                break;
                
            case 'error':
                console.error('WebSocket error:', message.message);
                this.showNotification('Error: ' + message.message, 'danger');
                break;
                
            default:
                console.log('Unknown message type:', message.type);
        }
    }

    updateStatus(status, text) {
        this.statusIndicator.className = `badge bg-${this.getStatusClass(status)}`;
        this.statusIndicator.innerHTML = `<i class="fas fa-circle"></i> ${text}`;
    }

    getStatusClass(status) {
        switch (status) {
            case 'connected': return 'success';
            case 'connecting': return 'warning';
            case 'disconnected': return 'danger';
            default: return 'secondary';
        }
    }

    toggleStream() {
        if (this.isStreaming) {
            this.stopStream();
        } else {
            this.startStream();
        }
    }

    startStream() {
        const url = this.isRawFeed ? this.rawStreamUrl : this.streamUrl;
        this.videoFeed.src = url + '?t=' + Date.now(); // Cache bust
        this.isStreaming = true;
        
        this.toggleStreamBtn.innerHTML = '<i class="fas fa-stop"></i> Stop';
        this.toggleStreamBtn.className = 'btn btn-outline-danger btn-sm';
        
        // Subscribe to frame updates via WebSocket for processed stream
        if (!this.isRawFeed) {
            this.sendWebSocketMessage({
                type: 'subscribe',
                subscription: 'stream'
            });
        }
    }

    stopStream() {
        this.videoFeed.src = '';
        this.isStreaming = false;
        
        this.toggleStreamBtn.innerHTML = '<i class="fas fa-play"></i> Start';
        this.toggleStreamBtn.className = 'btn btn-outline-primary btn-sm';
        
        // Unsubscribe from frame updates
        this.sendWebSocketMessage({
            type: 'unsubscribe',
            subscription: 'stream'
        });
    }

    toggleRawFeed() {
        this.isRawFeed = !this.isRawFeed;
        
        if (this.isRawFeed) {
            this.toggleRawBtn.innerHTML = '<i class="fas fa-eye"></i> Processed Feed';
            this.toggleRawBtn.className = 'btn btn-outline-warning btn-sm';
        } else {
            this.toggleRawBtn.innerHTML = '<i class="fas fa-eye-slash"></i> Raw Feed';
            this.toggleRawBtn.className = 'btn btn-outline-secondary btn-sm';
        }
        
        // Restart stream with new feed type
        if (this.isStreaming) {
            this.startStream();
        }
    }

    toggleFullscreen() {
        if (document.fullscreenElement) {
            document.exitFullscreen();
        } else {
            this.videoContainer.requestFullscreen();
        }
    }

    handleFullscreenChange() {
        if (document.fullscreenElement) {
            this.videoContainer.classList.add('fullscreen-video');
            this.fullscreenBtn.innerHTML = '<i class="fas fa-compress"></i> Exit Fullscreen';
        } else {
            this.videoContainer.classList.remove('fullscreen-video');
            this.fullscreenBtn.innerHTML = '<i class="fas fa-expand"></i> Fullscreen';
        }
    }

    updateDetections(data) {
        // Update live stats
        this.detectionCount.textContent = `${data.detection_count} Objects`;
        this.fpsDisplay.textContent = `${data.fps.toFixed(1)} FPS`;
        
        // Update total stats
        this.stats.totalDetections += data.detection_count;
        this.totalDetections.textContent = this.stats.totalDetections;
        
        // Update FPS history
        this.stats.fpsHistory.push(data.fps);
        if (this.stats.fpsHistory.length > 30) {
            this.stats.fpsHistory.shift();
        }
        this.stats.avgFps = this.stats.fpsHistory.reduce((a, b) => a + b, 0) / this.stats.fpsHistory.length;
        this.avgFps.textContent = this.stats.avgFps.toFixed(1);
        
        // Update detections list
        this.updateDetectionsList(data.detections);
    }

    updateDetectionsList(detections) {
        if (!detections || detections.length === 0) {
            this.detectionsListElement.innerHTML = `
                <div class="text-muted text-center py-3">
                    <i class="fas fa-search fa-2x"></i>
                    <p class="mt-2">No objects detected in current frame.</p>
                </div>
            `;
            return;
        }

        const detectionsHtml = detections.slice(0, 10).map(detection => {
            const confidenceClass = this.getConfidenceClass(detection.confidence);
            const bbox = detection.bbox.map(x => Math.round(x)).join(', ');
            
            return `
                <div class="detection-item p-3 border rounded mb-2 detection-${detection.class_name.toLowerCase()} new-detection">
                    <div class="d-flex justify-content-between align-items-start">
                        <div>
                            <h6 class="mb-1">
                                <i class="fas fa-crosshairs text-primary me-2"></i>
                                ${detection.class_name}
                                ${detection.track_id ? `<small class="text-muted">(ID: ${detection.track_id})</small>` : ''}
                            </h6>
                            <small class="text-muted">
                                <i class="fas fa-vector-square me-1"></i>
                                BBox: [${bbox}]
                                ${detection.area ? ` | Area: ${Math.round(detection.area)}px` : ''}
                            </small>
                        </div>
                        <span class="badge ${confidenceClass} confidence-badge">
                            ${(detection.confidence * 100).toFixed(1)}%
                        </span>
                    </div>
                </div>
            `;
        }).join('');

        this.detectionsListElement.innerHTML = detectionsHtml;
        
        // Fade out animation for old detections
        setTimeout(() => {
            const items = document.querySelectorAll('.detection-item.new-detection');
            items.forEach(item => item.classList.remove('new-detection'));
        }, 500);
    }

    getConfidenceClass(confidence) {
        if (confidence >= 0.8) return 'confidence-high bg-success';
        if (confidence >= 0.5) return 'confidence-medium bg-warning text-dark';
        return 'confidence-low bg-danger';
    }

    updateStats(data) {
        // Update system status
        if (data.camera) {
            const isConnected = data.camera.is_streaming;
            this.cameraStatus.innerHTML = isConnected ? 
                '<span class="badge bg-success">Connected</span>' : 
                '<span class="badge bg-danger">Disconnected</span>';
        }
        
        if (data.detector) {
            const isReady = data.detector.model !== null;
            this.detectorStatus.innerHTML = isReady ? 
                '<span class="badge bg-success">Ready</span>' : 
                '<span class="badge bg-warning">Loading</span>';
        }
        
        if (data.settings) {
            this.trackingStatus.innerHTML = data.settings.tracking_enabled ? 
                '<span class="badge bg-success">Enabled</span>' : 
                '<span class="badge bg-secondary">Disabled</span>';
                
            this.segmentationStatus.innerHTML = data.settings.segmentation_enabled ? 
                '<span class="badge bg-success">Enabled</span>' : 
                '<span class="badge bg-secondary">Disabled</span>';
        }
    }

    async applySettings() {
        const settings = {
            detection_confidence: parseFloat(this.confidenceThreshold.value),
            iou_threshold: parseFloat(this.iouThreshold.value),
            enable_tracking: this.enableTracking.checked,
            enable_segmentation: this.enableSegmentation.checked,
            model_size: this.modelSelect.value,
            camera_url: this.cameraUrl.value
        };

        try {
            this.applySettingsBtn.innerHTML = '<span class="spinner"></span> Applying...';
            this.applySettingsBtn.disabled = true;
            
            const response = await fetch('/config', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(settings)
            });
            
            if (response.ok) {
                const result = await response.json();
                this.showNotification('Settings applied successfully', 'success');
                
                // Restart stream if URL changed
                if (settings.camera_url !== this.cameraUrl.value && this.isStreaming) {
                    setTimeout(() => {
                        this.startStream();
                    }, 2000);
                }
            } else {
                throw new Error(`HTTP ${response.status}`);
            }
            
        } catch (error) {
            console.error('Settings update error:', error);
            this.showNotification('Failed to apply settings: ' + error.message, 'danger');
        } finally {
            this.applySettingsBtn.innerHTML = '<i class="fas fa-save"></i> Apply Settings';
            this.applySettingsBtn.disabled = false;
        }
    }

    async testCamera() {
        try {
            this.testCameraBtn.innerHTML = '<span class="spinner"></span> Testing...';
            this.testCameraBtn.disabled = true;
            
            const response = await fetch('/cli/status');
            const data = await response.json();
            
            if (data.camera_connected) {
                this.showNotification('Camera connection successful', 'success');
            } else {
                this.showNotification('Camera connection failed', 'warning');
            }
            
        } catch (error) {
            this.showNotification('Camera test failed: ' + error.message, 'danger');
        } finally {
            this.testCameraBtn.innerHTML = '<i class="fas fa-plug"></i> Test Connection';
            this.testCameraBtn.disabled = false;
        }
    }

    sendCliCommand() {
        const command = this.cliInput.value.trim();
        if (!command) return;
        
        // Add command to CLI output
        this.addCliOutput(`<div class="cli-prompt">$ ${command}</div>`, 'command');
        
        // Process command
        this.processCliCommand(command);
        
        // Clear input
        this.cliInput.value = '';
    }

    async processCliCommand(command) {
        const parts = command.split(' ');
        const cmd = parts[0].toLowerCase();
        
        switch (cmd) {
            case 'help':
                this.addCliOutput(this.getHelpText(), 'output');
                break;
                
            case 'status':
                try {
                    const response = await fetch('/cli/status');
                    const data = await response.json();
                    this.addCliOutput(`<pre>${JSON.stringify(data, null, 2)}</pre>`, 'output');
                } catch (error) {
                    this.addCliOutput(`Error: ${error.message}`, 'error');
                }
                break;
                
            case 'detect':
                try {
                    const response = await fetch('/cli/quick-detect');
                    const data = await response.json();
                    this.addCliOutput(`<pre>${JSON.stringify(data, null, 2)}</pre>`, 'output');
                } catch (error) {
                    this.addCliOutput(`Error: ${error.message}`, 'error');
                }
                break;
                
            case 'clear':
                this.cliOutput.innerHTML = '';
                break;
                
            default:
                this.addCliOutput(`Unknown command: ${cmd}. Type 'help' for available commands.`, 'error');
        }
    }

    getHelpText() {
        return `
            <div class="cli-output">
                <strong>Available Commands:</strong><br>
                <strong>help</strong> - Show this help message<br>
                <strong>status</strong> - Show system status<br>
                <strong>detect</strong> - Get current detection results<br>
                <strong>clear</strong> - Clear CLI output<br>
            </div>
        `;
    }

    addCliOutput(content, type) {
        const div = document.createElement('div');
        div.className = `cli-${type}`;
        div.innerHTML = content;
        this.cliOutput.appendChild(div);
        this.cliOutput.scrollTop = this.cliOutput.scrollHeight;
    }

    handleKeyboard(event) {
        // Keyboard shortcuts
        if (event.ctrlKey) {
            switch (event.key) {
                case ' ':
                    event.preventDefault();
                    this.toggleStream();
                    break;
                case 'f':
                    event.preventDefault();
                    this.toggleFullscreen();
                    break;
                case 'r':
                    event.preventDefault();
                    this.toggleRawFeed();
                    break;
            }
        }
        
        // CLI modal toggle
        if (event.key === 'F12') {
            event.preventDefault();
            const cliModal = new bootstrap.Modal(document.getElementById('cli-modal'));
            cliModal.show();
        }
    }

    showNotification(message, type = 'info') {
        // Create toast notification
        const toastHtml = `
            <div class="toast align-items-center text-white bg-${type} border-0" role="alert">
                <div class="d-flex">
                    <div class="toast-body">${message}</div>
                    <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast"></button>
                </div>
            </div>
        `;
        
        // Add to toast container (create if doesn't exist)
        let toastContainer = document.querySelector('.toast-container');
        if (!toastContainer) {
            toastContainer = document.createElement('div');
            toastContainer.className = 'toast-container position-fixed top-0 end-0 p-3';
            document.body.appendChild(toastContainer);
        }
        
        toastContainer.insertAdjacentHTML('beforeend', toastHtml);
        
        // Show toast
        const toastElement = toastContainer.lastElementChild;
        const toast = new bootstrap.Toast(toastElement);
        toast.show();
        
        // Remove after hidden
        toastElement.addEventListener('hidden.bs.toast', () => {
            toastElement.remove();
        });
    }

    loadSettings() {
        // Load settings from localStorage
        const savedSettings = localStorage.getItem('yolo-detector-settings');
        if (savedSettings) {
            try {
                const settings = JSON.parse(savedSettings);
                
                if (settings.confidence_threshold) {
                    this.confidenceThreshold.value = settings.confidence_threshold;
                    this.confidenceValue.textContent = settings.confidence_threshold.toFixed(2);
                }
                
                if (settings.iou_threshold) {
                    this.iouThreshold.value = settings.iou_threshold;
                    this.iouValue.textContent = settings.iou_threshold.toFixed(2);
                }
                
                if (settings.enable_tracking !== undefined) {
                    this.enableTracking.checked = settings.enable_tracking;
                }
                
                if (settings.enable_segmentation !== undefined) {
                    this.enableSegmentation.checked = settings.enable_segmentation;
                }
                
                if (settings.model_size) {
                    this.modelSelect.value = settings.model_size;
                }
                
                if (settings.camera_url) {
                    this.cameraUrl.value = settings.camera_url;
                }
                
            } catch (error) {
                console.error('Failed to load saved settings:', error);
            }
        }
    }

    saveSettings() {
        const settings = {
            confidence_threshold: parseFloat(this.confidenceThreshold.value),
            iou_threshold: parseFloat(this.iouThreshold.value),
            enable_tracking: this.enableTracking.checked,
            enable_segmentation: this.enableSegmentation.checked,
            model_size: this.modelSelect.value,
            camera_url: this.cameraUrl.value
        };
        
        localStorage.setItem('yolo-detector-settings', JSON.stringify(settings));
    }
}

// Initialize app when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    window.yoloApp = new YOLODetectorApp();
    
    // Save settings on page unload
    window.addEventListener('beforeunload', () => {
        if (window.yoloApp) {
            window.yoloApp.saveSettings();
        }
    });
});

// Initialize tooltips
document.addEventListener('DOMContentLoaded', function() {
    var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    var tooltipList = tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
});