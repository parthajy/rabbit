"""
Input processor router.

Takes any input (text, file path, bytes) and converts it to ProcessedInput
that the Rabbit pipeline can ingest.
"""

from __future__ import annotations

import mimetypes
from pathlib import Path

from rabbit.core.types import ProcessedInput


def process_input(input_data: str | Path | bytes, source: str = "unknown", metadata: dict | None = None) -> ProcessedInput:
    """Route input to the appropriate processor based on type.

    Args:
        input_data: Raw text string, file path, or bytes.
        source: Source label (meeting, email, slack, note, etc.)
        metadata: Additional metadata about the input.

    Returns:
        ProcessedInput with extracted text and metadata.
    """
    metadata = metadata or {}

    # Raw text string
    if isinstance(input_data, str) and not Path(input_data).exists():
        return ProcessedInput(
            text=input_data,
            source_type="text",
            metadata={"source": source, **metadata},
        )

    # File path
    path = Path(input_data) if isinstance(input_data, str) else None
    if path and path.exists():
        return _process_file(path, source, metadata)

    # Bytes — try to detect type
    if isinstance(input_data, bytes):
        return ProcessedInput(
            text=input_data.decode("utf-8", errors="replace"),
            source_type="text",
            metadata={"source": source, **metadata},
        )

    # Fallback: treat as text
    return ProcessedInput(
        text=str(input_data),
        source_type="text",
        metadata={"source": source, **metadata},
    )


def _process_file(path: Path, source: str, metadata: dict) -> ProcessedInput:
    """Process a file based on its extension/mime type."""
    suffix = path.suffix.lower()
    mime_type, _ = mimetypes.guess_type(str(path))
    metadata["filename"] = path.name
    metadata["source"] = source

    # Audio files
    if suffix in (".mp3", ".wav", ".m4a", ".ogg", ".flac", ".webm") or (mime_type and mime_type.startswith("audio/")):
        return _process_audio(path, metadata)

    # PDF
    if suffix == ".pdf":
        return _process_pdf(path, metadata)

    # Office documents
    if suffix in (".docx", ".doc", ".pptx", ".ppt", ".xlsx", ".xls"):
        return _process_document(path, metadata)

    # Images
    if suffix in (".png", ".jpg", ".jpeg", ".gif", ".bmp", ".webp", ".tiff") or (mime_type and mime_type.startswith("image/")):
        return _process_image(path, metadata)

    # Markdown
    if suffix in (".md", ".mdx"):
        return _process_markdown(path, metadata)

    # HTML
    if suffix in (".html", ".htm"):
        return _process_html(path, metadata)

    # Calendar
    if suffix == ".ics":
        return _process_calendar(path, metadata)

    # Email
    if suffix in (".eml", ".mbox"):
        return _process_email(path, metadata)

    # Code files
    if suffix in (".py", ".js", ".ts", ".tsx", ".jsx", ".go", ".rs", ".java", ".c", ".cpp", ".h", ".rb", ".php", ".swift", ".kt"):
        return _process_code(path, metadata)

    # Plain text / JSON / CSV — read as text
    text = path.read_text(encoding="utf-8", errors="replace")
    return ProcessedInput(
        text=text,
        source_type="text",
        metadata=metadata,
    )


# ── Individual Processors ──────────────────────────────────────────────────


def _process_audio(path: Path, metadata: dict) -> ProcessedInput:
    """Transcribe audio using faster-whisper."""
    try:
        from faster_whisper import WhisperModel

        model = WhisperModel("base", device="cpu", compute_type="int8")
        segments, info = model.transcribe(str(path), beam_size=5)

        text_parts = []
        for segment in segments:
            text_parts.append(segment.text)

        text = " ".join(text_parts).strip()
        metadata["duration_seconds"] = round(info.duration, 1)
        metadata["language"] = info.language

        return ProcessedInput(
            text=text,
            source_type="audio",
            metadata=metadata,
        )
    except ImportError:
        raise ImportError(
            "Audio processing requires faster-whisper. "
            "Install it: pip install faster-whisper"
        )


def _process_pdf(path: Path, metadata: dict) -> ProcessedInput:
    """Extract text from PDF using Docling."""
    try:
        from docling.document_converter import DocumentConverter

        converter = DocumentConverter()
        result = converter.convert(str(path))
        text = result.document.export_to_markdown()

        # Chunk long documents
        chunks = _chunk_text(text, max_chunk_size=2000) if len(text) > 3000 else []
        metadata["page_count"] = len(result.document.pages) if hasattr(result.document, "pages") else 0

        return ProcessedInput(
            text=text,
            source_type="pdf",
            metadata=metadata,
            chunks=chunks,
        )
    except ImportError:
        # Fallback to PyPDF2
        try:
            from PyPDF2 import PdfReader

            reader = PdfReader(str(path))
            text_parts = [page.extract_text() or "" for page in reader.pages]
            text = "\n\n".join(text_parts).strip()
            metadata["page_count"] = len(reader.pages)

            chunks = _chunk_text(text, max_chunk_size=2000) if len(text) > 3000 else []

            return ProcessedInput(
                text=text,
                source_type="pdf",
                metadata=metadata,
                chunks=chunks,
            )
        except ImportError:
            raise ImportError(
                "PDF processing requires docling or PyPDF2. "
                "Install: pip install docling  OR  pip install PyPDF2"
            )


def _process_document(path: Path, metadata: dict) -> ProcessedInput:
    """Extract text from Office documents using Docling."""
    try:
        from docling.document_converter import DocumentConverter

        converter = DocumentConverter()
        result = converter.convert(str(path))
        text = result.document.export_to_markdown()

        chunks = _chunk_text(text, max_chunk_size=2000) if len(text) > 3000 else []

        return ProcessedInput(
            text=text,
            source_type="document",
            metadata=metadata,
            chunks=chunks,
        )
    except ImportError:
        raise ImportError(
            "Document processing requires docling. "
            "Install it: pip install docling"
        )


def _process_image(path: Path, metadata: dict) -> ProcessedInput:
    """Extract text/understanding from images.

    Uses OCR (pytesseract) as default. ColPali for deeper understanding
    can be enabled separately.
    """
    try:
        from PIL import Image
        import pytesseract

        img = Image.open(path)
        text = pytesseract.image_to_string(img).strip()
        metadata["image_size"] = f"{img.width}x{img.height}"

        return ProcessedInput(
            text=text if text else f"[Image: {path.name} — no text extracted]",
            source_type="image",
            metadata=metadata,
        )
    except ImportError:
        return ProcessedInput(
            text=f"[Image: {path.name} — install pytesseract for OCR]",
            source_type="image",
            metadata=metadata,
        )


def _process_markdown(path: Path, metadata: dict) -> ProcessedInput:
    """Process markdown files (Obsidian vaults, docs, etc.)."""
    text = path.read_text(encoding="utf-8", errors="replace")

    # Extract wiki-links for Obsidian compatibility
    import re
    wiki_links = re.findall(r'\[\[(.*?)\]\]', text)
    if wiki_links:
        metadata["wiki_links"] = wiki_links

    chunks = _chunk_text(text, max_chunk_size=2000) if len(text) > 3000 else []

    return ProcessedInput(
        text=text,
        source_type="markdown",
        metadata=metadata,
        chunks=chunks,
    )


def _process_html(path: Path, metadata: dict) -> ProcessedInput:
    """Extract readable text from HTML."""
    try:
        from trafilatura import extract

        html_content = path.read_text(encoding="utf-8", errors="replace")
        text = extract(html_content) or ""

        return ProcessedInput(
            text=text,
            source_type="web",
            metadata=metadata,
        )
    except ImportError:
        # Basic fallback: strip HTML tags
        import re
        html_content = path.read_text(encoding="utf-8", errors="replace")
        text = re.sub(r'<[^>]+>', ' ', html_content)
        text = re.sub(r'\s+', ' ', text).strip()

        return ProcessedInput(
            text=text,
            source_type="web",
            metadata=metadata,
        )


def _process_calendar(path: Path, metadata: dict) -> ProcessedInput:
    """Extract events from .ics calendar files."""
    try:
        from icalendar import Calendar

        cal_text = path.read_bytes()
        cal = Calendar.from_ical(cal_text)

        events = []
        for component in cal.walk():
            if component.name == "VEVENT":
                summary = str(component.get("SUMMARY", ""))
                description = str(component.get("DESCRIPTION", ""))
                dtstart = component.get("DTSTART")
                dtend = component.get("DTEND")
                attendees = component.get("ATTENDEE", [])
                if not isinstance(attendees, list):
                    attendees = [attendees]

                event_text = f"Event: {summary}"
                if dtstart:
                    event_text += f"\nDate: {dtstart.dt}"
                if description:
                    event_text += f"\nDescription: {description}"
                if attendees:
                    event_text += f"\nAttendees: {', '.join(str(a) for a in attendees)}"
                events.append(event_text)

        text = "\n\n".join(events) if events else "[No events found]"
        metadata["event_count"] = len(events)

        return ProcessedInput(
            text=text,
            source_type="calendar",
            metadata=metadata,
        )
    except ImportError:
        raise ImportError(
            "Calendar processing requires icalendar. "
            "Install it: pip install icalendar"
        )


def _process_email(path: Path, metadata: dict) -> ProcessedInput:
    """Extract text from .eml email files."""
    import email
    from email import policy

    raw = path.read_bytes()
    msg = email.message_from_bytes(raw, policy=policy.default)

    subject = msg.get("Subject", "")
    sender = msg.get("From", "")
    to = msg.get("To", "")
    date = msg.get("Date", "")

    # Get body text
    body = ""
    if msg.is_multipart():
        for part in msg.walk():
            if part.get_content_type() == "text/plain":
                body = part.get_content()
                break
    else:
        body = msg.get_content()

    text = f"Subject: {subject}\nFrom: {sender}\nTo: {to}\nDate: {date}\n\n{body}"
    metadata["subject"] = subject
    metadata["from"] = sender

    return ProcessedInput(
        text=text,
        source_type="email",
        metadata=metadata,
    )


def _process_code(path: Path, metadata: dict) -> ProcessedInput:
    """Process code files — include filename and language context."""
    text = path.read_text(encoding="utf-8", errors="replace")
    metadata["language"] = path.suffix.lstrip(".")
    metadata["line_count"] = text.count("\n") + 1

    chunks = _chunk_text(text, max_chunk_size=2000) if len(text) > 3000 else []

    return ProcessedInput(
        text=f"File: {path.name}\n\n{text}",
        source_type="code",
        metadata=metadata,
        chunks=chunks,
    )


# ── Utilities ──────────────────────────────────────────────────────────────


def _chunk_text(text: str, max_chunk_size: int = 2000, overlap: int = 200) -> list[str]:
    """Split text into overlapping chunks at paragraph boundaries."""
    paragraphs = text.split("\n\n")
    chunks = []
    current_chunk = ""

    for para in paragraphs:
        if len(current_chunk) + len(para) > max_chunk_size and current_chunk:
            chunks.append(current_chunk.strip())
            # Keep overlap from end of previous chunk
            words = current_chunk.split()
            overlap_words = words[-overlap // 5:] if len(words) > overlap // 5 else []
            current_chunk = " ".join(overlap_words) + "\n\n" + para
        else:
            current_chunk += "\n\n" + para if current_chunk else para

    if current_chunk.strip():
        chunks.append(current_chunk.strip())

    return chunks
