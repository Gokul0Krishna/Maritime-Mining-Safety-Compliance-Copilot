import pypdfium2 
import pymupdf

class PDFParser:
    def __init__(self, file_path):
        self.file_path = file_path

    def parse_with_pypdfium2(self):
        pdf = pypdfium2.PdfDocument(self.file_path)
        text = ""
        for page in pdf:
            text += page.get_textpage().get_text_range()
        return text

    def parse_with_pymupdf(self):
        doc = pymupdf.open(self.file_path)
        text = ""
        for page in doc:
            text += page.get_text()
        return text

    def parse(self):
        try: 
            content = parse_with_pypdfium2()
            return content
        except Exception as e:
            try:
                content = parse_with_pymupdf()
                return content
            except Exception as e:
                raise ValueError("Unsupported parsing method. Choose 'pypdfium2' or 'pymupdf'.")


if __name__ == "__main__":
    file_path = "example.pdf"  # Replace with your PDF file path
    parser = PDFParser(file_path="data/raw/Circuarlegislative_25082026.pdf").parse()
    print(parser)
    parser = PDFParser(file_path="/home/gokul/Desktop/code/Maritime-Mining-Safety-Compliance-Copilot/data/raw/MSC-LEG-MEPC-TCC-FAL.1-Circ.1 - Interim Guidance To Facilitate Remote Sessions Of TheCommittees During The Covid-19 Pandem... (Secretariat).pdf").parse()
    print(parser)
    