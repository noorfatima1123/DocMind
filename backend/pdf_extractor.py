import PyPDF2
import pdfplumber


def extract_text_pypdf2(pdf_path: str) -> str:
    """
    PyPDF2 use karke PDF se text nikalta hai.
    Simple hai, lekin kabhi kabhi formatting garbar kar deta hai.
    """
    text = ""
    
    # PDF file open karo read-binary mode mein
    with open(pdf_path, "rb") as file:
        reader = PyPDF2.PdfReader(file)
        
        # Total pages print karo (debugging ke liye)
        total_pages = len(reader.pages)
        print(f"Total pages found: {total_pages}")
        
        # Har page se text extract karo
        for page_num in range(total_pages):
            page = reader.pages[page_num]
            page_text = page.extract_text()
            
            if page_text:
                text += page_text + "\n"
            
            print(f"Page {page_num + 1} done")
    
    return text


def extract_text_pdfplumber(pdf_path: str) -> str:
    """
    pdfplumber use karke PDF se text nikalta hai.
    Jyada accurate hai, tables bhi handle kar sakta hai.
    """
    text = ""
    
    with pdfplumber.open(pdf_path) as pdf:
        total_pages = len(pdf.pages)
        print(f"Total pages found: {total_pages}")
        
        for page_num, page in enumerate(pdf.pages):
            page_text = page.extract_text()
            
            if page_text:
                text += page_text + "\n"
            
            print(f"Page {page_num + 1} done")
    
    return text


def extract_text(pdf_path: str, method: str = "pdfplumber") -> str:
    """
    Convenience function — method choose karo 'pypdf2' ya 'pdfplumber'
    Default: pdfplumber (better accuracy)
    """
    if method == "pypdf2":
        return extract_text_pypdf2(pdf_path)
    elif method == "pdfplumber":
        return extract_text_pdfplumber(pdf_path)
    else:
        raise ValueError("Method must be 'pypdf2' or 'pdfplumber'")