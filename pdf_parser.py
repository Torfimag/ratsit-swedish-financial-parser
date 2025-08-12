import pdfplumber
import re
import pandas as pd
from pathlib import Path

class RatsitPDFParser:
    def __init__(self):
        self.data_pattern = re.compile(
            r'([A-Za-zÀ-ÿ\s\-]+),\s+([A-Za-zÀ-ÿ\s\-\d]+)\s+(\d+)\s+(\d+)\s+(\d+)\s+([NJ])\s+([\d\s\-]+)\s+([\d\s\-]+)'
        )
    
    def extract_postal_code_from_header(self, text):
        """Extract postal code from header like '167 72 Bromma'"""
        match = re.search(r'(\d{3}\s\d{2})\s+([A-Za-zÀ-ÿ]+)', text)
        if match:
            return match.group(1), match.group(2)
        return None, None
    
    def parse_pdf(self, pdf_path):
        """Parse a single PDF file and extract all person data"""
        results = []
        
        with pdfplumber.open(pdf_path) as pdf:
            for page in pdf.pages:
                text = page.extract_text()
                if not text:
                    continue
                
                lines = text.split('\n')
                postal_code, area_name = None, None
                
                # Find postal code and area from header
                for line in lines:
                    pc, an = self.extract_postal_code_from_header(line)
                    if pc:
                        postal_code, area_name = pc, an
                        break
                
                # Extract person data
                for line in lines:
                    if self.is_data_line(line):
                        person_data = self.parse_person_line(line, postal_code, area_name)
                        if person_data:
                            results.append(person_data)
        
        return results
    
    def is_data_line(self, line):
        """Check if line contains person data"""
        # Skip header lines and empty lines
        if not line.strip() or 'Namn, adress' in line or 'Å IÅ LR' in line:
            return False
            
        # Look for pattern: Name, Address followed by numbers
        # Example: "Kindström Magnus, Djupdalsvägen 114    53 23 80 N 932 500 -129 720"
        if ',' in line and re.search(r'\d+\s+\d{2}\s+\d+\s+[NJ]\s+', line):
            return True
            
        return False
    
    def parse_person_line(self, line, postal_code, area_name):
        """Parse a single line containing person data"""
        try:
            # Example line: "Kindström Magnus, Djupdalsvägen 114 53 23 80 N 932 500 -129 720"
            # Split on comma first to separate name from address+data
            if ',' not in line:
                return None
                
            name_part, rest = line.split(',', 1)
            name = name_part.strip()
            
            # Split rest into address and numeric data  
            rest = rest.strip()
            parts = rest.split()
            
            if len(parts) < 6:  # Need at least address + 5 numeric fields
                return None
            
            # Find where numbers start (age should be 2-digit number)
            address_parts = []
            data_start_idx = -1
            
            for i, part in enumerate(parts):
                if re.match(r'^\d{2}$', part) and i < len(parts) - 5:  # Age is 2 digits
                    # Check if next part is also 2-digit number (year)
                    if i + 1 < len(parts) and re.match(r'^\d{2}$', parts[i + 1]):
                        data_start_idx = i
                        break
                address_parts.append(part)
            
            if data_start_idx == -1:
                return None
                
            address = ' '.join(address_parts)
            data_parts = parts[data_start_idx:]
            
            if len(data_parts) < 6:
                return None
                
            try:
                age = int(data_parts[0])
                income_year = int(data_parts[1]) + 2000  # Convert 22,23 to 2022,2023
                salary_rank = int(data_parts[2])
                payment_remarks = data_parts[3]  # N or J
                
                # Salary and capital - combine all remaining parts and handle spaces/negatives
                salary_capital = ' '.join(data_parts[4:])
                # Split by significant whitespace to separate salary from capital
                amounts = re.split(r'\s{2,}', salary_capital)
                if len(amounts) < 2:
                    amounts = salary_capital.split()[-2:]  # Take last 2 numbers
                
                salary_str = amounts[0].replace(' ', '').replace(',', '')
                capital_str = amounts[1].replace(' ', '').replace(',', '') if len(amounts) > 1 else '0'
                
                # Handle negative values and dashes
                salary = 0
                capital = 0
                
                try:
                    salary = int(salary_str) if salary_str not in ['0', '—', ''] else 0
                except:
                    salary = 0
                    
                try:
                    capital = int(capital_str) if capital_str not in ['0', '—', ''] else 0
                except:
                    capital = 0
                
                return {
                    'name': name,
                    'address': address,
                    'postal_code': postal_code,
                    'area_name': area_name,
                    'age': age,
                    'income_year': income_year,
                    'salary_rank': salary_rank,
                    'payment_remarks': payment_remarks == 'J',  # True if 'J' (Yes)
                    'salary': salary,
                    'capital': capital
                }
            except (ValueError, IndexError) as e:
                print(f"Error parsing numeric data from line: {line[:50]}... - {e}")
                return None
                
        except Exception as e:
            print(f"Error parsing line: {line[:50]}... - {e}")
            return None
    
    def parse_all_pdfs(self, pdf_directory):
        """Parse all PDF files in the directory"""
        pdf_dir = Path(pdf_directory)
        all_data = []
        
        for pdf_file in pdf_dir.glob("*.pdf"):
            print(f"Parsing {pdf_file.name}...")
            try:
                data = self.parse_pdf(pdf_file)
                all_data.extend(data)
                print(f"Extracted {len(data)} records from {pdf_file.name}")
            except Exception as e:
                print(f"Error parsing {pdf_file.name}: {e}")
        
        return all_data

if __name__ == "__main__":
    parser = RatsitPDFParser()
    data = parser.parse_all_pdfs("pdfer")
    
    if data:
        df = pd.DataFrame(data)
        print(f"\nTotal records extracted: {len(df)}")
        print("\nSample data:")
        print(df.head())
        
        # Save to CSV for inspection
        df.to_csv("extracted_data.csv", index=False)
        print("\nData saved to extracted_data.csv")
    else:
        print("No data extracted")