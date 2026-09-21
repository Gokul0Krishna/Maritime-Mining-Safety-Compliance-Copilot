import re
from typing import Dict, List, Optional
import tiktoken
from langchain_text_splitters import RecursiveCharacterTextSplitter
from PDF_parser import PDFParser
from PDF_filter import PDFFilter

class HierarchicalDocumentChunker:

    def __init__(
        self,
        doc_type: str = "generic",
        max_chunk_tokens: int = 800,
        chunk_overlap_tokens: int = 100,
        embedding_model: str = "cl100k_base",
    ):
        """Args:

        doc_type: Domain target ('dgms', 'marpol', 'ports_act', or 'generic')
        max_chunk_tokens: Maximum token limit before secondary splitting is
        applied
        chunk_overlap_tokens: Token overlap for secondary recursive splitting
        embedding_model: Tiktoken tokenizer encoding name
        """
        self.doc_type = doc_type.lower()
        self.max_chunk_tokens = max_chunk_tokens
        self.chunk_overlap_tokens = chunk_overlap_tokens
        self.tokenizer = tiktoken.get_encoding(embedding_model)

        # Initialize secondary recursive splitter guardrail
        self.secondary_splitter = RecursiveCharacterTextSplitter.from_tiktoken_encoder(
            encoding_name=embedding_model,
            chunk_size=max_chunk_tokens,
            chunk_overlap=chunk_overlap_tokens,
            separators=["\n\n", "\n", ". ", "; ", " ", ""],
        )

        # Primary boundary regex patterns
        self.primary_patterns = {
            "dgms": r"(?=(?:^|\n)(?:###\s*)?(?:CIRCULAR\s+NO\.|DGMS\s*\(Tech\)|RECOMMENDATION\s+\d+|MAJOR\s+RECOMMENDATION))",
            "marpol": r"(?=(?:^|\n)(?:###\s*)?(?:REGULATION\s+\d+|ARTICLE\s+[IVXLCDM\d]+|ANNEX\s+[IVXLCDM\d]+))",
            "ports_act": r"(?=(?:^|\n)(?:###\s*)?(?:SECTION\s+\d+|CLAUSE\s+\d+|\d+\.\s+[A-Z]))",
            "generic": r"(?=(?:^|\n)#{1,3}\s+)",
        }

    def count_tokens(self, text: str) -> int:
        """Helper to count tokens using tiktoken."""
        return len(self.tokenizer.encode(text))

    def _extract_and_mask_tables(self, text: str) -> tuple[str, Dict[str, str]]:
        """Extracts Markdown/HTML tables to prevent primary splitters from breaking them

        apart.
        """
        table_map = {}
        # Matches Markdown tables (header, delimiter, and rows)
        table_pattern = re.compile(
            r"(\n(?:\|[^\n]+\|\r?\n)((?:\|[-:]+[-| :]*\|\r?\n))(?:\|[^\n]+\|\r?\n?)+)",
            re.MULTILINE,
        )

        def replace_table(match):
            key = f"__TABLE_PLACEHOLDER_{len(table_map)}__"
            table_map[key] = match.group(1)
            return f"\n\n{key}\n\n"

        masked_text = table_pattern.sub(replace_table, text)
        return masked_text, table_map

    def _split_primary_boundaries(self, text: str) -> List[str]:
        """Splits text according to domain-specific header/section boundaries."""
        pattern = self.primary_patterns.get(
            self.doc_type, self.primary_patterns["generic"]
        )
        # Split text while keeping non-empty strings
        raw_chunks = re.split(pattern, text, flags=re.IGNORECASE)
        return [c.strip() for c in raw_chunks if c and c.strip()]

    def _restore_tables(self, chunk: str, table_map: Dict[str, str]) -> str:
        """Restores table placeholders back to full table text."""
        for key, table_content in table_map.items():
            if key in chunk:
                chunk = chunk.replace(key, table_content.strip())
        return chunk

    def chunk_document(self, text: str) -> List[Dict[str, any]]:
        """Processes text through:

        1. Table masking (atomic preservation) 2. Primary domain header
        splitting 3. Secondary token size guardrail check + recursive splitting
        4. Re-inserting atomic tables
        """
        final_chunks = []

        # 1. Mask tables as atomic placeholders
        masked_text, table_map = self._extract_and_mask_tables(text)

        # 2. Apply Primary Boundary (Semantic/Header Split)
        primary_chunks = self._split_primary_boundaries(masked_text)

        # 3. Process each primary chunk against the secondary guardrail
        for i, chunk in enumerate(primary_chunks):
            # Restore tables before evaluating token count
            restored_chunk = self._restore_tables(chunk, table_map)
            token_count = self.count_tokens(restored_chunk)

            # Secondary Boundary (Token Limit Guardrail)
            if token_count > self.max_chunk_tokens:
                # If chunk is too large, recursively split it while preserving overlap
                sub_chunks = self.secondary_splitter.split_text(restored_chunk)
                for j, sub_c in enumerate(sub_chunks):
                    final_chunks.append(
                        {
                            "chunk_id": f"chunk_{i}_{j}",
                            "text": sub_c,
                            "tokens": self.count_tokens(sub_c),
                            "split_type": "secondary_recursive",
                            "doc_type": self.doc_type,
                        }
                    )
            else:
                final_chunks.append(
                    {
                        "chunk_id": f"chunk_{i}",
                        "text": restored_chunk,
                        "tokens": token_count,
                        "split_type": "primary_semantic",
                        "doc_type": self.doc_type,
                    }
                )

        return final_chunks

if __name__ == "__main__":
    pdf_path = "/home/gokul/Desktop/code/Maritime-Mining-Safety-Compliance-Copilot/data/raw/MSC-LEG-MEPC-TCC-FAL.1-Circ.1 - Interim Guidance To Facilitate Remote Sessions Of TheCommittees During The Covid-19 Pandem... (Secretariat).pdf"
    parser = PDFParser(pdf_path)
    raw_text = parser.parse()
    cleaned_text = PDFFilter.clean_text(raw_text)
    chunker = HierarchicalDocumentChunker(doc_type="generic")
    chunks = chunker.chunk_document(cleaned_text)
    print(chunks)
