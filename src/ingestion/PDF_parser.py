import fitz  # PyMuPDF
import pypdfium2


class PDFParser:
    def __init__(self, file_path):
        self.file_path = file_path

    def parse_with_pypdfium2(self):
        pdf = pypdfium2.PdfDocument(self.file_path)
        text = ""
        for page in pdf:
            text += page.get_textpage().get_text_range()

        if not text.strip():
            raise ValueError("pypdfium2 extracted no text from PDF.")
        return text

    def parse_with_pymupdf(self):
        doc = fitz.open(self.file_path)
        text = ""
        for page in doc:
            text += page.get_text()

        if not text.strip():
            raise ValueError("PyMuPDF extracted no text from PDF.")
        return text

    def parse_with_ocr(self):
        """Fallback method using PyMuPDF to render pages to images and pytesseract for OCR."""
        import pytesseract
        from PIL import Image
        import io

        doc = fitz.open(self.file_path)
        ocr_text = ""

        for page in doc:
            # Render page to image (DPI 300 for good OCR accuracy)
            pix = page.get_pixmap(dpi=300)
            img = Image.open(io.BytesIO(pix.tobytes("png")))
            
            # Extract text using Tesseract OCR
            text = pytesseract.image_to_string(img)
            ocr_text += text + "\n"

        if not ocr_text.strip():
            raise ValueError("OCR failed to extract text from PDF.")
        return ocr_text

    def parse(self):
        # 1. Try pypdfium2 (Fastest digital text extraction)
        try:
            return self.parse_with_pypdfium2()
        except Exception:
            pass

        # 2. Try PyMuPDF (Digital text extraction fallback)
        try:
            return self.parse_with_pymupdf()
        except Exception:
            pass

        # 3. Fallback to OCR for scanned documents
        try:
            print("Digital text extraction failed. Falling back to OCR...")
            return self.parse_with_ocr()
        except Exception as ocr_err:
            raise ValueError(
                f"Failed to extract text from '{self.file_path}'. "
                "Document appears to be empty, unreadable, or scanned (and OCR failed)."
            ) from ocr_err


if __name__ == "__main__":
    file_path = "example.pdf"  # Replace with your PDF file path
    parser = PDFParser(file_path="data/raw/Circuarlegislative_25082026.pdf").parse()
    print(parser)
    