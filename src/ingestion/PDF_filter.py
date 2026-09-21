from PDF_parser import PDFParser
import re

class PDFFilter:

    @staticmethod
    def fix_hyphenated_line_breaks(text: str) -> str:
        """Fixes hyphenated word breaks split across lines (e.g., regu-\nlation -> regulation)."""
        # Matches lowercase letters ending with a hyphen at line end, followed by lowercase letters on the next line
        return re.sub(r"([a-z|A-Z]+)-\n\s*([a-z|A-Z]+)", r"\1\2", text)

    @staticmethod
    def strip_headers_footers_watermarks(
        text: str, watermarks: list[str] = None
    ) -> str:
        """Strips standalone page numbers, common header/footer patterns, and repeated watermarks."""
        lines = text.splitlines()
        cleaned_lines = []

        # Default watermark pattern if none provided
        if watermarks is None:
            watermarks = [
                r"DRAFT",
                r"CONFIDENTIAL",
                r"FOR INTERNAL USE ONLY",
                r"DO NOT COPY",
            ]

        # Compile watermark regex (case-insensitive)
        watermark_pattern = re.compile(
            r"^\s*(" + "|".join(watermarks) + r")\s*$", re.IGNORECASE
        )

        # Regex for page numbers (e.g., "Page 1", "1 of 10", "- 5 -", standalone numbers)
        page_num_pattern = re.compile(
            r"^\s*(page\s*\d+(\s*of\s*\d+)?|-?\s*\d+\s*-?)\s*$", re.IGNORECASE
        )

        for line in lines:
            line_str = line.strip()

            # Skip empty lines, standalone page numbers, and standalone watermarks
            if not line_str:
                continue
            if page_num_pattern.match(line_str):
                continue
            if watermark_pattern.match(line_str):
                continue

            cleaned_lines.append(line)

        # Rejoin text
        cleaned_text = "\n".join(cleaned_lines)

        # Remove inline repeated watermarks if they appear mid-sentence
        for wm in watermarks:
            cleaned_text = re.sub(
                rf"\b{wm}\b", "", cleaned_text, flags=re.IGNORECASE
            )

        return cleaned_text

    @staticmethod
    def standardize_section_headers(text: str) -> str:
        """Standardizes headers such as Section 1, Annex I/V/VI, Circular No. X into uppercase markdown format."""
        patterns = [
            # Matches: Section 1, Section 10.2, Section A
            (
                r"(?i)\bsection\s+(\d+|[A-Z]+(\.\d+)*)\b",
                lambda m: f"\n\n### SECTION {m.group(1).upper()}\n",
            ),
            # Matches: Annex I, Annex V, Annex VI, Annex 1, Annex A
            (
                r"(?i)\bannex\s+([IVXLCDM\d]+|[A-Z])\b",
                lambda m: f"\n\n### ANNEX {m.group(1).upper()}\n",
            ),
            # Matches: Circular No. 12/2024, Circular No 5, Circular No. A-1
            (
                r"(?i)\bcircular\s+no\.?\s*([\w\/-]+)\b",
                lambda m: f"\n\n### CIRCULAR NO. {m.group(1).upper()}\n",
            ),
            # Matches: Chapter 1, Chapter IV
            (
                r"(?i)\bchapter\s+([IVXLCDM\d]+)\b",
                lambda m: f"\n\n### CHAPTER {m.group(1).upper()}\n",
            ),
        ]

        cleaned_text = text
        for pattern, replacement in patterns:
            cleaned_text = re.sub(pattern, replacement, cleaned_text)

        # Normalize multiple consecutive blank lines to double newlines
        cleaned_text = re.sub(r"\n{3,}", "\n\n", cleaned_text)

        return cleaned_text.strip()

    @classmethod
    def clean_text(cls, text: str, custom_watermarks: list[str] = None) -> str:
        """Applies all cleaning steps in optimal order."""
        # 1. Fix hyphenation across lines before stripping line breaks
        text = cls.fix_hyphenated_line_breaks(text)

        # 2. Remove page numbers, headers/footers, and watermarks
        text = cls.strip_headers_footers_watermarks(
            text, watermarks=custom_watermarks
        )

        # 3. Standardize section headers into clean markdown headings
        text = cls.standardize_section_headers(text)

        return text
    
if __name__ == "__main__":
    # Example usage
    pdf_path = "/home/gokul/Desktop/code/Maritime-Mining-Safety-Compliance-Copilot/data/raw/MSC-LEG-MEPC-TCC-FAL.1-Circ.1 - Interim Guidance To Facilitate Remote Sessions Of TheCommittees During The Covid-19 Pandem... (Secretariat).pdf"
    parser = PDFParser(pdf_path)
    raw_text = parser.parse()
    cleaned_text = PDFFilter.clean_text(raw_text)
    print(cleaned_text)