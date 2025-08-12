#!/usr/bin/env python3

import pdfplumber
import re

# Let's debug the actual amounts parsing from one PDF
def debug_amounts():
    pdf_path = "pdfer/Magnus+Kindström+Bromma+sida+62.pdf"
    
    with pdfplumber.open(pdf_path) as pdf:
        page = pdf.pages[1]  # Page 2 has the data
        text = page.extract_text()
        
        lines = text.split('\n')
        for line_num, line in enumerate(lines):
            if len(line.strip()) > 50 and ',' in line and re.search(r'\d.*[NJ]', line):
                print(f"\nLine {line_num}: {line[:100]}...")
                
                # Try to extract amounts using similar logic
                # Look for pattern after N or J
                after_payment = re.split(r'\b[NJ]\b', line)
                if len(after_payment) > 1:
                    amounts_part = after_payment[1][:50]  # First 50 chars after N/J
                    print(f"Amounts part: '{amounts_part}'")
                    
                    # Find all number sequences
                    numbers = re.findall(r'-?\d+(?:\s+\d+)*|\d+', amounts_part)
                    print(f"Found numbers: {numbers}")
                    
                    # Try to reconstruct Swedish format
                    for num_str in numbers[:3]:  # First few numbers
                        if ' ' in num_str:
                            reconstructed = num_str.replace(' ', '')
                            print(f"'{num_str}' -> {reconstructed} ({int(reconstructed):,} SEK)")
                        elif num_str.isdigit() and len(num_str) >= 3:
                            print(f"'{num_str}' -> {int(num_str):,} SEK")
                            
                if line_num > 20:  # Just first few lines
                    break

if __name__ == "__main__":
    debug_amounts()