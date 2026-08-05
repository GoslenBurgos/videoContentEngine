import os
from pathlib import Path
from bs4 import BeautifulSoup
import pypdf

class SourceParser:
    """Parses text content from raw text, Markdown files, PDFs, or HTML documents."""

    @staticmethod
    def parse_file(file_path: str | Path) -> str:
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")
        
        ext = path.suffix.lower()
        if ext in [".md", ".txt"]:
            with open(path, "r", encoding="utf-8", errors="ignore") as f:
                return f.read()
        elif ext == ".pdf":
            return SourceParser._parse_pdf(path)
        elif ext in [".html", ".htm"]:
            return SourceParser._parse_html(path)
        else:
            raise ValueError(f"Unsupported file extension: {ext}")

    @staticmethod
    def _parse_pdf(path: Path) -> str:
        text_content = []
        reader = pypdf.PdfReader(path)
        for page in reader.pages:
            extracted = page.extract_text()
            if extracted:
                text_content.append(extracted)
        return "\n\n".join(text_content)

    @staticmethod
    def _parse_html(path: Path) -> str:
        with open(path, "r", encoding="utf-8", errors="ignore") as f:
            soup = BeautifulSoup(f.read(), "html.parser")
            # Remove scripts and styling elements
            for element in soup(["script", "style", "nav", "footer", "header"]):
                element.extract()
            return soup.get_text(separator="\n", strip=True)

    @staticmethod
    def clean_text(raw_text: str) -> str:
        """Removes excessive whitespace and standardizes formatting."""
        lines = [line.strip() for line in raw_text.splitlines() if line.strip()]
        return "\n".join(lines)
