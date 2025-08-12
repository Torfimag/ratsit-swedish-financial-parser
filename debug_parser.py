#!/usr/bin/env python3
"""Debug script to test PDF parsing"""

from pdf_parser import RatsitPDFParser

def debug_pdf():
    parser = RatsitPDFParser()
    
    # Test with one PDF first
    pdf_path = "pdfer/Magnus+Kindström+Bromma+sida+62.pdf"
    
    print(f"Debugging {pdf_path}")
    
    import pdfplumber
    with pdfplumber.open(pdf_path) as pdf:
        for page_num, page in enumerate(pdf.pages):
            print(f"\n=== PAGE {page_num + 1} ===")
            text = page.extract_text()
            if text:
                lines = text.split('\n')
                for i, line in enumerate(lines):
                    if line.strip():
                        print(f"{i:3d}: {line}")
                        if parser.is_data_line(line):
                            print(f"     ^^ DATA LINE DETECTED")
                            result = parser.parse_person_line(line, "167 72", "Bromma")
                            if result:
                                print(f"     -> PARSED: {result['name']} - {result['salary']} SEK")
                            else:
                                print(f"     -> PARSE FAILED")

if __name__ == "__main__":
    debug_pdf()