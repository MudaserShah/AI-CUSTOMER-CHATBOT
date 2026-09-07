import logging
import re
from typing import Dict, List, Optional

from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter


logger = logging.getLogger(__name__)

CHUNK_SIZE = 500
CHUNK_OVERLAP = 50

PAGE_MARKER_RE = re.compile(r"<!--\s*page:(\d+)\s*-->")
ROW_MARKER_RE = re.compile(r"<!--\s*row:(\d+)\s*-->")


def generate_markdown(docs: List[Document], file_name: str) -> str:
    """
    Convert loaded LangChain Documents into one markdown string.

    PDF documents:
        <!-- page:1 -->
        Content...

    CSV documents:
        <!-- row:1 -->
        Content...

    DOCX, TXT and Markdown documents:
        Content...

    Page numbers are only added when a real page number exists.
    CSV row numbers are kept separate from page numbers.
    """

    parts: List[str] = []

    for doc in docs:
        text = doc.page_content.strip()

        if not text:
            continue

        page_number = doc.metadata.get("page_number")
        row_number = doc.metadata.get("row_number")

        if page_number is not None:
            parts.append(
                f"<!-- page:{page_number} -->\n\n{text}"
            )

        elif row_number is not None:
            parts.append(
                f"<!-- row:{row_number} -->\n\n{text}"
            )

        else:
            parts.append(text)

    markdown = "\n\n---\n\n".join(parts)

    logger.info(
        "Generated markdown for '%s' (%d characters)",
        file_name,
        len(markdown),
    )

    return markdown


def smart_chunk(
    markdown_text: str,
    chunk_size: int = CHUNK_SIZE,
    chunk_overlap: int = CHUNK_OVERLAP,
) -> List[Dict]:
    """
    Split markdown into chunks while preserving page and row information.

    Tables are kept as atomic chunks and are never split.

    Returns:
        [
            {
                "text": "...",
                "page_number": 1,
                "row_number": None,
                "is_table": False,
            }
        ]
    """

    chunks: List[Dict] = []

    # First try to process page-based content.
    page_segments = PAGE_MARKER_RE.split(markdown_text)

    if len(page_segments) > 1:
        _process_marked_segments(
            page_segments,
            marker_type="page",
            chunks=chunks,
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
        )
    else:
        # No PDF page markers.
        # Process CSV row markers if they exist.
        row_segments = ROW_MARKER_RE.split(markdown_text)

        if len(row_segments) > 1:
            _process_marked_segments(
                row_segments,
                marker_type="row",
                chunks=chunks,
                chunk_size=chunk_size,
                chunk_overlap=chunk_overlap,
            )
        else:
            # DOCX / TXT / Markdown
            _chunk_section(
                text=markdown_text,
                page_number=None,
                row_number=None,
                chunk_size=chunk_size,
                chunk_overlap=chunk_overlap,
                result=chunks,
            )

    return [
        chunk
        for chunk in chunks
        if chunk["text"].strip()
    ]


def _process_marked_segments(
    segments: List[str],
    marker_type: str,
    chunks: List[Dict],
    chunk_size: int,
    chunk_overlap: int,
) -> None:
    """
    Process content separated by page or row markers.

    re.split() with a capturing group produces:

        [before_marker, marker_value, content, marker_value, content, ...]
    """

    # Content before the first marker.
    if segments[0].strip():
        _chunk_section(
            text=segments[0],
            page_number=None,
            row_number=None,
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            result=chunks,
        )

    i = 1

    while i + 1 < len(segments):
        try:
            marker_value = int(segments[i])
        except ValueError:
            marker_value = None

        content = segments[i + 1]

        if marker_type == "page":
            page_number = marker_value
            row_number = None
        else:
            page_number = None
            row_number = marker_value

        if content.strip():
            _chunk_section(
                text=content,
                page_number=page_number,
                row_number=row_number,
                chunk_size=chunk_size,
                chunk_overlap=chunk_overlap,
                result=chunks,
            )

        i += 2


def _chunk_section(
    text: str,
    page_number: Optional[int],
    row_number: Optional[int],
    chunk_size: int,
    chunk_overlap: int,
    result: List[Dict],
) -> None:
    """
    Process one document section.

    Table rows are collected and kept together as one chunk.

    All other text is treated as prose and split using
    RecursiveCharacterTextSplitter.
    """

    lines = text.splitlines()

    prose_buffer: List[str] = []
    table_buffer: List[str] = []

    in_table = False

    def flush_prose() -> None:
        """Split the current prose buffer into chunks."""

        if not prose_buffer:
            return

        prose_text = "\n".join(prose_buffer).strip()
        prose_buffer.clear()

        if not prose_text:
            return

        splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            separators=[
                "\n\n",
                "\n",
                ". ",
                " ",
                "",
            ],
        )

        for chunk_text in splitter.split_text(prose_text):
            if not chunk_text.strip():
                continue

            result.append(
                {
                    "text": chunk_text.strip(),
                    "page_number": page_number,
                    "row_number": row_number,
                    "is_table": False,
                }
            )

    def flush_table() -> None:
        """Add the complete table as one atomic chunk."""

        if not table_buffer:
            return

        table_text = "\n".join(table_buffer).strip()
        table_buffer.clear()

        if not table_text:
            return

        result.append(
            {
                "text": table_text,
                "page_number": page_number,
                "row_number": row_number,
                "is_table": True,
            }
        )

    for line in lines:
        is_table_row = _is_table_row(line)

        if is_table_row:
            if not in_table:
                flush_prose()
                in_table = True

            table_buffer.append(line)

        else:
            if in_table:
                flush_table()
                in_table = False

            prose_buffer.append(line)

    # Flush remaining content.
    if in_table:
        flush_table()
    else:
        flush_prose()


def _is_table_row(line: str) -> bool:
    """
    Return True if a line looks like a markdown table row.
    """

    stripped = line.strip()

    if stripped.startswith("|"):
        return True

    # Handles separator rows such as:
    # |------|------|
    if "|" in stripped and re.fullmatch(r"[-:| ]+", stripped):
        return True

    return False