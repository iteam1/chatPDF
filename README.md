# chatPDF
Chat with your PDF

## Overview
`chatPDF` is a lightweight Flask web app that lets you upload a PDF and view it in the browser with smooth scrolling, zoom controls, and a text layer for selectable/copyable text. It also provides an AI chat endpoint to ask questions about the PDF content using OpenAI.

## Features
- **File upload** with validation (`.pdf`) and size limit (default 50MB).
- **In-browser PDF viewer** powered by PDF.js with zoom, page navigation, and text layer rendering.
- **Recent files list** for quick access after uploads.
- **AI chat endpoint** (`/chat`) that calls OpenAI to generate responses using page context.

## Core Technologies
- **Flask** web server and routing in `app.py`.
  - Routes include `"/"` (upload), `"/view/<filename>"` (viewer), `"/pdf/<filename>"` (serve file), and `"/chat"` (AI API).
  - Uses `render_template_string` with embedded HTML templates: `UPLOAD_TEMPLATE` and `VIEWER_TEMPLATE`.
- **PDF.js** for client-side rendering of PDFs in the `VIEWER_TEMPLATE`.
  - Loaded via CDN and configured with `pdfjsLib.GlobalWorkerOptions.workerSrc`.
- **OpenAI (1.x SDK)** for AI chat in `app.py`.
  - Modern usage: `from openai import OpenAI` and `client.chat.completions.create(...)`.
  - API key loaded from environment via `python-dotenv`.
- **File handling**
  - Secure filenames via `werkzeug.utils.secure_filename`.
  - Upload folder configured by `UPLOAD_FOLDER` (default `uploads/`).
  - Max upload size set by `MAX_CONTENT_LENGTH`.

## Project Structure
```
chatPDF/
├─ app.py                 # Main Flask app, routes, embedded templates
├─ requirements.txt       # Python dependencies
├─ README.md              # This file
├─ .env                   # Environment variables (not committed)
└─ uploads/               # Created at runtime for uploaded PDFs
```

## Setup
1. Create and activate a virtual environment (recommended).
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Create a `.env` file (or copy yours) with:
   ```env
   OPENAI_API_KEY=your_openai_api_key
   ```

## Running
```bash
python app.py
```
Then open http://localhost:5000

Optional (production-style run):
```bash
pip install gunicorn
gunicorn app:app
```

## Key Endpoints
- **GET/POST `"/"`**: Upload page. Accepts a `.pdf` and redirects to the viewer.
- **GET `"/view/<filename>"`**: Viewer page (HTML) that uses PDF.js to render the PDF.
- **GET `"/pdf/<filename>"`**: Serves the raw PDF file from `uploads/`.
- **POST `"/chat"`**: JSON endpoint for AI chat. Body includes `message`, `history`, and `context` (e.g., `currentPage`, `totalPages`, `selectedText`). Returns `{ response: string }`.

## Notes
- Ensure `uploads/` is writable. The app creates it if missing.
- The OpenAI key is required only for the `/chat` endpoint; viewing PDFs works without it.
- Flask’s built-in server is for development. Use a WSGI server (e.g., Gunicorn) for production.
