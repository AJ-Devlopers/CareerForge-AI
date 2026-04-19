from pypdf import PdfReader
from io import BytesIO


def extract_text_from_pdf(file):

    try:
        # 🔹 Read file bytes
        pdf_bytes = file.file.read()

        # 🔹 Load PDF
        reader = PdfReader(BytesIO(pdf_bytes))

        text = ""

        # 🔹 Extract text from each page
        for page in reader.pages:
            extracted = page.extract_text()
            if extracted:
                text += extracted + "\n"

        return text.lower()

    except Exception:
        return ""