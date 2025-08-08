#!/usr/bin/env python3
"""
PDF Viewer Application with Upload and Scroll Navigation
Based on design.md specifications
"""
import os
import uuid
import openai
from dotenv import load_dotenv
from flask import Flask, render_template_string, request, redirect, url_for, send_file, send_from_directory, flash, jsonify
from werkzeug.utils import secure_filename

# Load environment variables from .env file
load_dotenv()

app = Flask(__name__)
app.secret_key = 'pdf_viewer_secret_key_2024'

# Configuration
UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'pdf'}
MAX_CONTENT_LENGTH = 50 * 1024 * 1024  # 50MB max file size

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = MAX_CONTENT_LENGTH

# Create upload directory if it doesn't exist
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# HTML Templates
UPLOAD_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>PDF Viewer - Upload</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            display: flex;
            align-items: center;
            justify-content: center;
        }
        
        .upload-container {
            background: white;
            padding: 2rem;
            border-radius: 15px;
            box-shadow: 0 20px 40px rgba(0,0,0,0.1);
            text-align: center;
            max-width: 500px;
            width: 90%;
        }
        
        .upload-container h1 {
            color: #333;
            margin-bottom: 1rem;
            font-size: 2rem;
        }
        
        .upload-container p {
            color: #666;
            margin-bottom: 2rem;
            font-size: 1.1rem;
        }
        
        .upload-area {
            border: 3px dashed #ddd;
            border-radius: 10px;
            padding: 2rem;
            margin-bottom: 1rem;
            transition: all 0.3s ease;
            cursor: pointer;
        }
        
        .upload-area:hover {
            border-color: #667eea;
            background-color: #f8f9ff;
        }
        
        .upload-area.dragover {
            border-color: #667eea;
            background-color: #f0f4ff;
        }
        
        .upload-icon {
            font-size: 3rem;
            color: #ddd;
            margin-bottom: 1rem;
        }
        
        .upload-text {
            color: #666;
            font-size: 1.1rem;
            margin-bottom: 1rem;
        }
        
        input[type="file"] {
            display: none;
        }
        
        .file-input-label {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 12px 30px;
            border-radius: 25px;
            cursor: pointer;
            display: inline-block;
            font-weight: 500;
            transition: transform 0.2s ease;
        }
        
        .file-input-label:hover {
            transform: translateY(-2px);
        }
        
        .upload-btn {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border: none;
            padding: 12px 30px;
            border-radius: 25px;
            cursor: pointer;
            font-size: 1rem;
            font-weight: 500;
            transition: transform 0.2s ease;
            margin-top: 1rem;
        }
        
        .upload-btn:hover {
            transform: translateY(-2px);
        }
        
        .upload-btn:disabled {
            background: #ccc;
            cursor: not-allowed;
            transform: none;
        }
        
        .file-info {
            background: #f8f9fa;
            padding: 1rem;
            border-radius: 8px;
            margin: 1rem 0;
            display: none;
        }
        
        .file-name {
            font-weight: 500;
            color: #333;
        }
        
        .file-size {
            color: #666;
            font-size: 0.9rem;
        }
        
        .flash-messages {
            margin-bottom: 1rem;
        }
        
        .flash-message {
            padding: 10px;
            border-radius: 5px;
            margin-bottom: 10px;
        }
        
        .flash-error {
            background-color: #f8d7da;
            color: #721c24;
            border: 1px solid #f5c6cb;
        }
        
        .flash-success {
            background-color: #d4edda;
            color: #155724;
            border: 1px solid #c3e6cb;
        }
        
        .recent-files {
            margin-top: 2rem;
            text-align: left;
        }
        
        .recent-files h3 {
            color: #333;
            margin-bottom: 1rem;
        }
        
        .recent-file {
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 0.5rem;
            border-bottom: 1px solid #eee;
        }
        
        .recent-file:last-child {
            border-bottom: none;
        }
        
        .recent-file a {
            color: #667eea;
            text-decoration: none;
            font-weight: 500;
        }
        
        .recent-file a:hover {
            text-decoration: underline;
        }
        
        .file-date {
            color: #999;
            font-size: 0.8rem;
        }
    </style>
</head>
<body>
    <div class="upload-container">
        <h1>📄 PDF Viewer</h1>
        <p>Upload a PDF file to start viewing</p>
        
        <div class="flash-messages">
            {% with messages = get_flashed_messages() %}
                {% if messages %}
                    {% for message in messages %}
                        <div class="flash-message flash-error">{{ message }}</div>
                    {% endfor %}
                {% endif %}
            {% endwith %}
        </div>
        
        <form method="post" enctype="multipart/form-data" id="uploadForm">
            <div class="upload-area" id="uploadArea">
                <div class="upload-icon">📁</div>
                <div class="upload-text">Drag and drop your PDF here</div>
                <label for="file" class="file-input-label">Choose File</label>
                <input type="file" name="file" id="file" accept=".pdf" required>
            </div>
            
            <div class="file-info" id="fileInfo">
                <div class="file-name" id="fileName"></div>
                <div class="file-size" id="fileSize"></div>
            </div>
            
            <button type="submit" class="upload-btn" id="uploadBtn" disabled>Upload & View PDF</button>
        </form>
        
        {% if recent_files %}
        <div class="recent-files">
            <h3>Recent Files</h3>
            {% for file in recent_files %}
            <div class="recent-file">
                <a href="{{ url_for('view_pdf', filename=file.name) }}">{{ file.display_name }}</a>
                <span class="file-date">{{ file.date }}</span>
            </div>
            {% endfor %}
        </div>
        {% endif %}
    </div>
    
    <script>
        const fileInput = document.getElementById('file');
        const uploadArea = document.getElementById('uploadArea');
        const fileInfo = document.getElementById('fileInfo');
        const fileName = document.getElementById('fileName');
        const fileSize = document.getElementById('fileSize');
        const uploadBtn = document.getElementById('uploadBtn');
        
        // File input change handler
        fileInput.addEventListener('change', handleFileSelect);
        
        // Drag and drop handlers
        uploadArea.addEventListener('dragover', handleDragOver);
        uploadArea.addEventListener('dragleave', handleDragLeave);
        uploadArea.addEventListener('drop', handleDrop);
        uploadArea.addEventListener('click', () => fileInput.click());
        
        function handleFileSelect(e) {
            const file = e.target.files[0];
            if (file) {
                displayFileInfo(file);
            }
        }
        
        function handleDragOver(e) {
            e.preventDefault();
            uploadArea.classList.add('dragover');
        }
        
        function handleDragLeave(e) {
            e.preventDefault();
            uploadArea.classList.remove('dragover');
        }
        
        function handleDrop(e) {
            e.preventDefault();
            uploadArea.classList.remove('dragover');
            
            const files = e.dataTransfer.files;
            if (files.length > 0) {
                const file = files[0];
                if (file.type === 'application/pdf') {
                    fileInput.files = files;
                    displayFileInfo(file);
                } else {
                    alert('Please select a PDF file');
                }
            }
        }
        
        function displayFileInfo(file) {
            fileName.textContent = file.name;
            fileSize.textContent = formatFileSize(file.size);
            fileInfo.style.display = 'block';
            uploadBtn.disabled = false;
        }
        
        function formatFileSize(bytes) {
            if (bytes === 0) return '0 Bytes';
            const k = 1024;
            const sizes = ['Bytes', 'KB', 'MB', 'GB'];
            const i = Math.floor(Math.log(bytes) / Math.log(k));
            return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
        }
    </script>
</body>
</html>
"""

VIEWER_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>PDF Viewer - {{ filename }}</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        body {
            margin: 0;
            padding: 0;
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: #2c2c2c;
            color: #ffffff;
            overflow: hidden;
            display: flex;
        }
        
        .header {
            background-color: #1e1e2e;
            color: white;
            padding: 0.3rem 0.8rem;
            position: fixed;
            top: 0;
            left: 0;
            right: 0;
            z-index: 1000;
            display: flex;
            justify-content: space-between;
            align-items: center;
            box-shadow: 0 1px 5px rgba(0,0,0,0.3);
            height: 40px;
        }
        
        .header-left {
            display: flex;
            align-items: center;
            gap: 1rem;
        }
        
        .back-btn {
            background: #667eea;
            color: white;
            border: none;
            padding: 6px 12px;
            border-radius: 4px;
            cursor: pointer;
            text-decoration: none;
            display: inline-block;
            font-size: 0.9rem;
        }
        
        .back-btn:hover {
            background: #5a6fd8;
        }
        
        .title {
            font-size: 1rem;
            font-weight: 500;
        }
        
        .header-right {
            display: flex;
            align-items: center;
            gap: 1rem;
        }
        
        .page-info {
            background: rgba(255,255,255,0.1);
            padding: 4px 12px;
            border-radius: 15px;
            font-size: 0.8rem;
        }
        
        .zoom-controls {
            display: flex;
            gap: 5px;
        }
        
        .zoom-btn {
            background: rgba(255,255,255,0.1);
            color: white;
            border: none;
            padding: 4px 8px;
            border-radius: 4px;
            cursor: pointer;
            font-size: 0.8rem;
        }
        
        .zoom-btn:hover {
            background: rgba(255,255,255,0.2);
        }
        
        .viewer-container {
            margin-top: 40px;
            padding: 0.5rem;
            display: flex;
            justify-content: center;
            min-height: calc(100vh - 40px);
            flex: 1;
            overflow: auto;
        }

        .pdf-container {
            max-width: 100%;
            width: 100%;
            background: #2f3349;
            border-radius: 6px;
            box-shadow: none;
            overflow: auto;
            display: flex;
            justify-content: center;
            align-items: center;
            padding: 10px;
            max-height: calc(100vh - 60px);
        }
        
        #pdfCanvas {
            display: block;
            max-width: none;
            height: auto;
            margin: 0 auto;
        }
        
        .pdf-page-container {
            position: relative;
            display: inline-block;
        }
        
        .text-layer {
            position: absolute;
            left: 0;
            top: 0;
            right: 0;
            bottom: 0;
            overflow: hidden;
            line-height: 1.0;
            pointer-events: none;
        }
        
        .text-layer > span {
            color: transparent;
            position: absolute;
            white-space: pre;
            cursor: text;
            transform-origin: 0% 0%;
            pointer-events: auto;
            user-select: text;
            -webkit-user-select: text;
            -moz-user-select: text;
            -ms-user-select: text;
        }
        
        .text-layer ::selection {
            background: rgba(0, 0, 255, 0.3);
        }
        
        .text-layer ::-moz-selection {
            background: rgba(0, 0, 255, 0.3);
        }
        
        .loading {
            text-align: center;
            color: white;
            font-size: 1.2rem;
            padding: 3rem;
        }
        
        .scroll-indicator {
            position: fixed;
            right: 2rem;
            top: 50%;
            transform: translateY(-50%);
            background: rgba(0,0,0,0.7);
            color: white;
            padding: 1rem;
            border-radius: 10px;
            font-size: 0.9rem;
            z-index: 100;
            opacity: 0;
            transition: opacity 0.3s ease;
        }
        
        .scroll-indicator.show {
            opacity: 1;
        }
        
        .progress-bar {
            position: fixed;
            top: 40px;
            left: 0;
            height: 1px;
            background: #667eea;
            transition: width 0.3s ease;
            z-index: 999;
        }

        /* Chatbot Panel Styles */
        .chat-panel {
            width: 300px;
            height: 100vh;
            background: #1e1e2e;
            border-right: 1px solid #3a3a4a;
            display: flex;
            flex-direction: column;
            transition: transform 0.3s ease;
            z-index: 500;
        }

        .chat-panel.collapsed {
            transform: translateX(-270px);
        }

        .chat-header {
            padding: 0.6rem 0.8rem;
            background: #2a2a3a;
            border-bottom: 1px solid #3a3a4a;
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-top: 40px;
            font-size: 0.9rem;
        }

        .chat-toggle {
            position: absolute;
            right: -25px;
            top: 50px;
            background: #667eea;
            color: white;
            border: none;
            padding: 6px 5px;
            border-radius: 0 4px 4px 0;
            cursor: pointer;
            font-size: 12px;
            z-index: 501;
        }

        .chat-messages {
            flex: 1;
            overflow-y: auto;
            padding: 0.6rem;
            display: flex;
            flex-direction: column;
            gap: 0.6rem;
        }

        .message {
            max-width: 85%;
            padding: 0.75rem;
            border-radius: 12px;
            font-size: 0.9rem;
            line-height: 1.4;
        }

        .message.user {
            background: #667eea;
            color: white;
            align-self: flex-end;
            margin-left: auto;
        }

        .message.assistant {
            background: #3a3a4a;
            color: #e0e0e0;
            align-self: flex-start;
        }

        .message.system {
            background: #2a4a2a;
            color: #90ee90;
            align-self: center;
            font-size: 0.8rem;
            font-style: italic;
        }

        .chat-input-container {
            padding: 0.6rem;
            border-top: 1px solid #3a3a4a;
            background: #2a2a3a;
        }

        .chat-input {
            width: 100%;
            padding: 0.5rem;
            border: 1px solid #3a3a4a;
            border-radius: 6px;
            background: #1e1e2e;
            color: white;
            font-size: 0.85rem;
            resize: none;
            min-height: 32px;
            max-height: 80px;
        }

        .chat-input:focus {
            outline: none;
            border-color: #667eea;
        }

        .chat-send {
            margin-top: 0.4rem;
            width: 100%;
            padding: 0.5rem;
            background: #667eea;
            color: white;
            border: none;
            border-radius: 6px;
            cursor: pointer;
            font-size: 0.85rem;
            transition: background 0.2s;
        }

        .chat-send:hover {
            background: #5a6fd8;
        }

        .chat-send:disabled {
            background: #4a4a5a;
            cursor: not-allowed;
        }

        .main-content {
            flex: 1;
            display: flex;
            flex-direction: column;
        }
    </style>
</head>
<body>
    <!-- Main Content -->
    <div class="main-content">
        <div class="header">
        <div class="header-left">
            <a href="{{ url_for('index') }}" class="back-btn">← Back</a>
            <div class="title">📄 {{ filename }}</div>
        </div>
        <div class="header-right">
            <div class="page-info">
                Page <span id="currentPage">1</span> of <span id="totalPages">-</span>
            </div>
            <div class="zoom-controls">
                <button class="zoom-btn" onclick="zoomOut()">-</button>
                <span class="zoom-btn" id="zoomLevel">100%</span>
                <button class="zoom-btn" onclick="zoomIn()">+</button>
                <button class="zoom-btn" onclick="resetZoom()">Fit</button>
            </div>
        </div>
    </div>
    
    <div class="progress-bar" id="progressBar"></div>
    
    <div class="viewer-container">
        <div class="pdf-container">
            <div class="loading" id="loading">Loading PDF...</div>
            <div class="pdf-page-container" id="pageContainer" style="display: none;">
                <canvas id="pdfCanvas"></canvas>
                <div class="text-layer" id="textLayer"></div>
            </div>
        </div>
    </div>
    
    <div class="scroll-indicator" id="scrollIndicator">
        <div>Scroll to navigate</div>
        <div>↑ Previous page</div>
        <div>↓ Next page</div>
    </div>
    </div> <!-- End main-content -->
    
    <!-- Chat Panel -->
    <div class="chat-panel" id="chatPanel">
        <button class="chat-toggle" onclick="toggleChat()">💬</button>
        <div class="chat-header">
            <h3>PDF Assistant</h3>
            <button onclick="clearChat()" style="background: none; border: none; color: #ccc; cursor: pointer;">🗑️</button>
        </div>
        <div class="chat-messages" id="chatMessages">
            <div class="message system">Hi! I can help you understand this PDF. Ask me questions about the content, request summaries, or discuss specific sections.</div>
        </div>
        <div class="chat-input-container">
            <textarea class="chat-input" id="chatInput" placeholder="Ask about this PDF..." rows="2"></textarea>
            <button class="chat-send" id="chatSend" onclick="sendMessage()">Send</button>
        </div>
    </div>
    
    <!-- PDF.js Library -->
    <script src="https://cdnjs.cloudflare.com/ajax/libs/pdf.js/3.11.174/pdf.min.js"></script>
    
    <script>
        // PDF.js setup
        pdfjsLib.GlobalWorkerOptions.workerSrc = 'https://cdnjs.cloudflare.com/ajax/libs/pdf.js/3.11.174/pdf.worker.min.js';
        
        let pdfDoc = null;
        let currentPage = 1;
        let scale = 1.2;
        let canvas = document.getElementById('pdfCanvas');
        let ctx = canvas.getContext('2d');
        let isRendering = false;
        
        // Load PDF
        const url = '/pdf/{{ filename }}';
        
        pdfjsLib.getDocument(url).promise.then(function(pdf) {
            pdfDoc = pdf;
            document.getElementById('totalPages').textContent = pdf.numPages;
            document.getElementById('loading').style.display = 'none';
            document.getElementById('pageContainer').style.display = 'block';
            
            // Render first page
            renderPage(1);
            
            // Show scroll indicator briefly
            showScrollIndicator();
        }).catch(function(error) {
            console.error('Error loading PDF:', error);
            document.getElementById('loading').textContent = 'Error loading PDF';
        });
        
        function renderPage(pageNum) {
            if (isRendering) return;
            isRendering = true;
            
            pdfDoc.getPage(pageNum).then(function(page) {
                // Clear canvas first
                ctx.clearRect(0, 0, canvas.width, canvas.height);
                
                // Get base viewport at scale 1.0 for consistent sizing
                const baseViewport = page.getViewport({scale: 1.0});
                
                // Calculate render scale for quality
                const devicePixelRatio = window.devicePixelRatio || 1;
                const renderScale = scale * 2; // Higher resolution for crisp rendering
                
                // Get viewport for rendering (high resolution)
                const renderViewport = page.getViewport({scale: renderScale});
                
                // Set canvas internal size (for rendering quality)
                canvas.height = renderViewport.height;
                canvas.width = renderViewport.width;
                
                // Set canvas display size (for visual zoom)
                const displayWidth = baseViewport.width * scale;
                const displayHeight = baseViewport.height * scale;
                
                canvas.style.width = displayWidth + 'px';
                canvas.style.height = displayHeight + 'px';
                
                // Reset context transform
                ctx.setTransform(1, 0, 0, 1, 0, 0);
                
                const renderContext = {
                    canvasContext: ctx,
                    viewport: renderViewport
                };
                
                // Render canvas
                const renderTask = page.render(renderContext);
                
                // Render text layer for selection
                const textLayerDiv = document.getElementById('textLayer');
                textLayerDiv.innerHTML = ''; // Clear previous text
                
                // Set text layer size to match canvas display size
                textLayerDiv.style.width = displayWidth + 'px';
                textLayerDiv.style.height = displayHeight + 'px';
                
                // Render text layer using PDF.js renderTextLayer function
                page.getTextContent().then(function(textContent) {
                    const viewport = page.getViewport({scale: scale});
                    
                    // Clear previous text layer
                    textLayerDiv.innerHTML = '';
                    
                    // Use PDF.js built-in text layer rendering
                    pdfjsLib.renderTextLayer({
                        textContent: textContent,
                        container: textLayerDiv,
                        viewport: viewport,
                        textDivs: []
                    }).promise.then(function() {
                        // After rendering, make all text spans selectable
                        const textSpans = textLayerDiv.querySelectorAll('span');
                        textSpans.forEach(function(span) {
                            span.style.color = 'transparent';
                            span.style.userSelect = 'text';
                            span.style.cursor = 'text';
                            span.style.pointerEvents = 'auto';
                        });
                    }).catch(function(error) {
                        console.log('Text layer rendering failed, falling back to manual method');
                        
                        // Fallback to manual text positioning
                        textContent.items.forEach(function(textItem) {
                            if (textItem.str.trim() === '') return;
                            
                            const span = document.createElement('span');
                            span.textContent = textItem.str;
                            span.style.position = 'absolute';
                            span.style.color = 'transparent';
                            span.style.cursor = 'text';
                            span.style.userSelect = 'text';
                            span.style.pointerEvents = 'auto';
                            span.style.whiteSpace = 'pre';
                            span.style.margin = '0';
                            span.style.padding = '0';
                            span.style.lineHeight = '1';
                            
                            // Simple positioning based on viewport scale
                            const transform = textItem.transform;
                            const fontSize = Math.abs(transform[3]);
                            const x = transform[4];
                            const y = viewport.height - transform[5];
                            
                            span.style.left = x + 'px';
                            span.style.top = (y - fontSize) + 'px';
                            span.style.fontSize = fontSize + 'px';
                            
                            if (textItem.width) {
                                span.style.width = textItem.width + 'px';
                            }
                            
                            textLayerDiv.appendChild(span);
                        });
                    });
                });
                
                renderTask.promise.then(function() {
                    isRendering = false;
                    updatePageInfo(pageNum);
                    updateProgressBar();
                });
            });
        }
        
        function updatePageInfo(pageNum) {
            currentPage = pageNum;
            document.getElementById('currentPage').textContent = pageNum;
        }
        
        function updateProgressBar() {
            const progress = (currentPage / pdfDoc.numPages) * 100;
            document.getElementById('progressBar').style.width = progress + '%';
        }
        
        function zoomIn() {
            scale *= 1.25;
            if (scale > 3) scale = 3;
            updateZoomLevel();
            renderPage(currentPage);
            updateCursor();
        }
        
        function zoomOut() {
            scale *= 0.8;
            if (scale < 0.5) scale = 0.5;
            updateZoomLevel();
            renderPage(currentPage);
            updateCursor();
        }
        
        function resetZoom() {
            scale = 1.2;
            updateZoomLevel();
            renderPage(currentPage);
            updateCursor();
        }
        
        function updateZoomLevel() {
            document.getElementById('zoomLevel').textContent = Math.round(scale * 100) + '%';
        }
        
        function nextPage() {
            if (currentPage < pdfDoc.numPages) {
                renderPage(currentPage + 1);
            }
        }
        
        function prevPage() {
            if (currentPage > 1) {
                renderPage(currentPage - 1);
            }
        }
        
        function showScrollIndicator() {
            const indicator = document.getElementById('scrollIndicator');
            indicator.classList.add('show');
            setTimeout(() => {
                indicator.classList.remove('show');
            }, 3000);
        }
        
        // Improved scroll-based navigation
        let scrollTimeout;
        let lastScrollTop = 0;
        let scrollAccumulator = 0;
        let isScrollNavigating = false;
        
        window.addEventListener('wheel', function(e) {
            e.preventDefault(); // Prevent default page scrolling
            
            // Accumulate scroll delta for more responsive navigation
            scrollAccumulator += e.deltaY;
            
            clearTimeout(scrollTimeout);
            
            // Lower threshold for more responsive navigation
            const threshold = 100;
            
            if (Math.abs(scrollAccumulator) > threshold && !isScrollNavigating) {
                isScrollNavigating = true;
                
                if (scrollAccumulator > 0) {
                    // Scrolling down - next page
                    nextPage();
                } else {
                    // Scrolling up - previous page
                    prevPage();
                }
                
                scrollAccumulator = 0;
                
                // Reset navigation lock after shorter delay
                setTimeout(() => {
                    isScrollNavigating = false;
                }, 300);
            }
            
            // Reset accumulator if no scrolling for a while
            scrollTimeout = setTimeout(() => {
                scrollAccumulator = 0;
            }, 500);
        }, { passive: false });
        
        // Fallback for touch devices and other scroll events
        window.addEventListener('scroll', function() {
            const scrollTop = window.pageYOffset || document.documentElement.scrollTop;
            const scrollDelta = scrollTop - lastScrollTop;
            
            clearTimeout(scrollTimeout);
            scrollTimeout = setTimeout(function() {
                if (Math.abs(scrollDelta) > 30 && !isScrollNavigating) { // Lower threshold
                    isScrollNavigating = true;
                    
                    if (scrollDelta > 0) {
                        nextPage();
                    } else {
                        prevPage();
                    }
                    
                    setTimeout(() => {
                        isScrollNavigating = false;
                    }, 300);
                }
                lastScrollTop = scrollTop;
            }, 100); // Shorter debounce
        });
        
        // Keyboard shortcuts
        document.addEventListener('keydown', function(e) {
            switch(e.key) {
                case 'ArrowLeft':
                case 'ArrowUp':
                case 'PageUp':
                    e.preventDefault();
                    prevPage();
                    break;
                case 'ArrowRight':
                case 'ArrowDown':
                case 'PageDown':
                    e.preventDefault();
                    nextPage();
                    break;
                case '+':
                    if (e.ctrlKey) {
                        e.preventDefault();
                        zoomIn();
                    }
                    break;
                case '-':
                    if (e.ctrlKey) {
                        e.preventDefault();
                        zoomOut();
                    }
                    break;
                case '0':
                    if (e.ctrlKey) {
                        e.preventDefault();
                        resetZoom();
                    }
                    break;
            }
        });
        
        // Initialize zoom level display
        updateZoomLevel();
        
        // Drag-to-pan functionality for zoomed PDFs
        let isDragging = false;
        let dragStartX = 0;
        let dragStartY = 0;
        let scrollStartX = 0;
        let scrollStartY = 0;
        
        const pageContainer = document.getElementById('pageContainer');
        
        pageContainer.addEventListener('mousedown', function(e) {
            // Only enable dragging when zoomed in and not selecting text
            if (scale > 1.2 && !e.target.closest('.text-layer')) {
                isDragging = true;
                pageContainer.style.cursor = 'grabbing';
                
                dragStartX = e.clientX;
                dragStartY = e.clientY;
                
                const container = pageContainer.parentElement;
                scrollStartX = container.scrollLeft;
                scrollStartY = container.scrollTop;
                
                // Disable scroll-based page navigation while dragging
                isScrollNavigating = true;
                
                e.preventDefault();
                e.stopPropagation();
            }
        });
        
        pageContainer.addEventListener('mousemove', function(e) {
            if (isDragging) {
                const deltaX = e.clientX - dragStartX;
                const deltaY = e.clientY - dragStartY;
                
                const container = pageContainer.parentElement;
                
                // Apply both horizontal and vertical scrolling
                const newScrollLeft = Math.max(0, scrollStartX - deltaX);
                const newScrollTop = Math.max(0, scrollStartY - deltaY);
                
                container.scrollLeft = newScrollLeft;
                container.scrollTop = newScrollTop;
                
                e.preventDefault();
                e.stopPropagation();
            } else if (scale > 1.2 && !e.target.closest('.text-layer')) {
                pageContainer.style.cursor = 'grab';
            } else {
                pageContainer.style.cursor = 'default';
            }
        });
        
        pageContainer.addEventListener('mouseup', function(e) {
            if (isDragging) {
                isDragging = false;
                pageContainer.style.cursor = scale > 1.2 ? 'grab' : 'default';
                
                // Re-enable scroll-based page navigation after a delay
                setTimeout(() => {
                    isScrollNavigating = false;
                }, 500);
                
                e.preventDefault();
                e.stopPropagation();
            }
        });
        
        pageContainer.addEventListener('mouseleave', function(e) {
            if (isDragging) {
                isDragging = false;
                pageContainer.style.cursor = scale > 1.2 ? 'grab' : 'default';
                
                // Re-enable scroll-based page navigation after a delay
                setTimeout(() => {
                    isScrollNavigating = false;
                }, 500);
            }
        });
        
        // Touch support for mobile devices
        let touchStartX = 0;
        let touchStartY = 0;
        let touchScrollStartX = 0;
        let touchScrollStartY = 0;
        
        canvas.addEventListener('touchstart', function(e) {
            if (scale > 1.2 && e.touches.length === 1) {
                const touch = e.touches[0];
                touchStartX = touch.clientX;
                touchStartY = touch.clientY;
                
                const container = canvas.parentElement;
                touchScrollStartX = container.scrollLeft;
                touchScrollStartY = container.scrollTop;
                
                e.preventDefault();
            }
        }, { passive: false });
        
        canvas.addEventListener('touchmove', function(e) {
            if (scale > 1.2 && e.touches.length === 1) {
                const touch = e.touches[0];
                const deltaX = touch.clientX - touchStartX;
                const deltaY = touch.clientY - touchStartY;
                
                const container = canvas.parentElement;
                container.scrollLeft = touchScrollStartX - deltaX;
                container.scrollTop = touchScrollStartY - deltaY;
                
                e.preventDefault();
            }
        }, { passive: false });
        
        // Update cursor when zoom changes
        function updateCursor() {
            if (scale > 1.2) {
                pageContainer.style.cursor = 'grab';
            } else {
                pageContainer.style.cursor = 'default';
            }
        }

        // Chatbot functionality
        let chatHistory = [];
        let isChatCollapsed = false;

        function toggleChat() {
            const chatPanel = document.getElementById('chatPanel');
            isChatCollapsed = !isChatCollapsed;
            
            if (isChatCollapsed) {
                chatPanel.classList.add('collapsed');
            } else {
                chatPanel.classList.remove('collapsed');
            }
        }

        function clearChat() {
            const chatMessages = document.getElementById('chatMessages');
            chatMessages.innerHTML = '<div class="message system">Hi! I can help you understand this PDF. Ask me questions about the content, request summaries, or discuss specific sections.</div>';
            chatHistory = [];
        }

        function addMessage(content, type) {
            const chatMessages = document.getElementById('chatMessages');
            const messageDiv = document.createElement('div');
            messageDiv.className = `message ${type}`;
            messageDiv.textContent = content;
            chatMessages.appendChild(messageDiv);
            chatMessages.scrollTop = chatMessages.scrollHeight;
        }

        function sendMessage() {
            const chatInput = document.getElementById('chatInput');
            const chatSend = document.getElementById('chatSend');
            const message = chatInput.value.trim();
            
            if (!message) return;
            
            // Add user message
            addMessage(message, 'user');
            chatHistory.push({role: 'user', content: message});
            
            // Clear input and disable send button
            chatInput.value = '';
            chatSend.disabled = true;
            chatSend.textContent = 'Sending...';
            
            // Get current PDF context
            const pdfContext = {
                filename: '{{ filename }}',
                currentPage: currentPage,
                totalPages: pdfDoc ? pdfDoc.numPages : 0,
                selectedText: window.getSelection().toString()
            };
            
            // Send to backend
            fetch('/chat', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    message: message,
                    history: chatHistory,
                    context: pdfContext
                })
            })
            .then(response => response.json())
            .then(data => {
                if (data.response) {
                    addMessage(data.response, 'assistant');
                    chatHistory.push({role: 'assistant', content: data.response});
                } else {
                    addMessage('Sorry, I encountered an error. Please try again.', 'system');
                }
            })
            .catch(error => {
                console.error('Chat error:', error);
                addMessage('Sorry, I encountered an error. Please try again.', 'system');
            })
            .finally(() => {
                chatSend.disabled = false;
                chatSend.textContent = 'Send';
            });
        }

        // Handle Enter key in chat input
        document.getElementById('chatInput').addEventListener('keydown', function(e) {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                sendMessage();
            }
        });
    </script>
</body>
</html>
"""

@app.route('/')
def index():
    # Get list of uploaded files
    recent_files = []
    if os.path.exists(UPLOAD_FOLDER):
        files = os.listdir(UPLOAD_FOLDER)
        pdf_files = [f for f in files if f.lower().endswith('.pdf')]
        
        for filename in sorted(pdf_files, key=lambda x: os.path.getmtime(os.path.join(UPLOAD_FOLDER, x)), reverse=True)[:5]:
            file_path = os.path.join(UPLOAD_FOLDER, filename)
            file_stat = os.stat(file_path)
            
            # Create display name (remove UUID prefix if present)
            display_name = filename
            if '_' in filename and len(filename.split('_')[0]) == 36:  # UUID length
                display_name = '_'.join(filename.split('_')[1:])
            
            recent_files.append({
                'name': filename,
                'display_name': display_name,
                'date': os.path.getmtime(file_path)
            })
    
    return render_template_string(UPLOAD_TEMPLATE, recent_files=recent_files)

@app.route('/', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        flash('No file selected')
        return redirect(request.url)
    
    file = request.files['file']
    if file.filename == '':
        flash('No file selected')
        return redirect(request.url)
    
    if file and allowed_file(file.filename):
        # Generate unique filename to prevent conflicts
        original_filename = secure_filename(file.filename)
        unique_filename = f"{uuid.uuid4()}_{original_filename}"
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], unique_filename)
        
        try:
            file.save(file_path)
            return redirect(url_for('view_pdf', filename=unique_filename))
        except Exception as e:
            flash(f'Error uploading file: {str(e)}')
            return redirect(request.url)
    else:
        flash('Invalid file type. Please upload a PDF file.')
        return redirect(request.url)

@app.route('/view/<filename>')
def view_pdf(filename):
    file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    if not os.path.exists(file_path):
        flash('File not found')
        return redirect(url_for('index'))
    
    # Create display name (remove UUID prefix if present)
    display_name = filename
    if '_' in filename and len(filename.split('_')[0]) == 36:  # UUID length
        display_name = '_'.join(filename.split('_')[1:])
    
    return render_template_string(VIEWER_TEMPLATE, filename=filename, display_name=display_name)

@app.route('/pdf/<filename>')
def serve_pdf(filename):
    try:
        file_path = os.path.join(UPLOAD_FOLDER, filename)
        if not os.path.exists(file_path):
            print(f"PDF file not found: {file_path}")
            return "PDF file not found", 404
        
        print(f"Serving PDF: {file_path}")
        return send_from_directory(UPLOAD_FOLDER, filename, mimetype='application/pdf')
    except Exception as e:
        print(f"Error serving PDF {filename}: {e}")
        return f"Error serving PDF: {str(e)}", 500

@app.route('/chat', methods=['POST'])
def chat():
    try:
        data = request.get_json()
        message = data.get('message', '')
        history = data.get('history', [])
        context = data.get('context', {})
        
        # Build context-aware prompt
        system_prompt = f"""You are a helpful PDF assistant. You're helping the user understand a PDF document.

Current PDF Context:
- Filename: {context.get('filename', 'Unknown')}
- Current Page: {context.get('currentPage', 1)} of {context.get('totalPages', 'Unknown')}
- Selected Text: {context.get('selectedText', 'None')}

You can help with:
- Explaining content and concepts
- Summarizing sections or pages
- Answering questions about the document
- Discussing selected text
- Providing context and analysis

Be concise, helpful, and focus on the PDF content. If the user asks about specific pages or sections, acknowledge the current page context."""

        # Prepare messages for GPT
        messages = [{"role": "system", "content": system_prompt}]
        
        # Add conversation history (limit to last 10 messages to avoid token limits)
        recent_history = history[-10:] if len(history) > 10 else history
        messages.extend(recent_history)
        
        # Add current message
        messages.append({"role": "user", "content": message})
        
        # Use OpenAI API for real GPT responses
        try:
            # Get API key from environment
            api_key = os.getenv('OPENAI_API_KEY')
            
            if not api_key:
                response = "⚠️ OpenAI API key not found. Please set OPENAI_API_KEY in your .env file to enable AI chat."
            else:
                # Initialize OpenAI client with modern approach
                from openai import OpenAI
                client = OpenAI(api_key=api_key)
                
                # Make API call to OpenAI using new client
                completion = client.chat.completions.create(
                    model="gpt-3.5-turbo",
                    messages=messages,
                    max_tokens=500,
                    temperature=0.7
                )
                
                response = completion.choices[0].message.content.strip()
                
        except Exception as openai_error:
            print(f"OpenAI API error: {openai_error}")
            error_msg = str(openai_error).lower()
            
            # Handle specific error types
            if 'authentication' in error_msg or 'api key' in error_msg:
                response = "🔑 Invalid OpenAI API key. Please check your OPENAI_API_KEY in the .env file."
            elif 'rate limit' in error_msg or 'quota' in error_msg:
                response = "⏱️ OpenAI API rate limit exceeded. Please try again in a moment."
            elif 'connection' in error_msg or 'network' in error_msg:
                response = "🌐 Network connection issue. Please check your internet connection and try again."
            else:
                # Fallback to enhanced context-aware responses
                if context.get('selectedText'):
                    selected = context['selectedText'][:200]
                    response = f"I can see you've selected: \"{selected}{'...' if len(context['selectedText']) > 200 else ''}\"\n\nWhat would you like me to explain about this selection? (Note: AI chat temporarily unavailable)"
                elif 'summary' in message.lower():
                    response = f"I'd be happy to provide a summary of page {context.get('currentPage', 1)} of this document. What specific section interests you? (Note: AI chat temporarily unavailable)"
                elif 'explain' in message.lower():
                    response = "I can help explain concepts from this PDF. Could you point me to the specific section or concept you'd like me to clarify? (Note: AI chat temporarily unavailable)"
                else:
                    response = f"I'm here to help you understand this PDF document. Currently viewing page {context.get('currentPage', 1)} of {context.get('totalPages', '?')}. What would you like to know? (Note: AI chat temporarily unavailable)"
        
        return jsonify({'response': response})
        
    except Exception as e:
        print(f"Chat error: {e}")
        return jsonify({'error': 'Failed to process chat request'}), 500

def main():
    print("🚀 Starting PDF Viewer Application...")
    print("📁 Upload folder:", os.path.abspath(UPLOAD_FOLDER))
    print("📖 Open your browser and go to: http://localhost:5000")
    print("✨ Features: File upload, scroll navigation, zoom controls")
    print("🔧 Press Ctrl+C to stop the server")
    
    try:
        app.run(host='0.0.0.0', port=5000, debug=False)
    except KeyboardInterrupt:
        print("\n👋 Server stopped")

if __name__ == "__main__":
    main()
