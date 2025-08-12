import pdfplumber
import re
import pandas as pd
from pathlib import Path

class ImprovedRatsitParser:
    def __init__(self):
        pass
        
    def extract_table_data(self, pdf_path):
        """Extract data using pdfplumber's table extraction"""
        results = []
        
        with pdfplumber.open(pdf_path) as pdf:
            for page in pdf.pages:
                # Extract tables
                tables = page.extract_tables()
                
                # Also try to extract text and look for patterns
                text = page.extract_text()
                if text:
                    # Look for postal code and area name
                    postal_code, area_name = self.extract_postal_code_from_text(text)
                    
                    # Process tables
                    for table in tables:
                        if table and len(table) > 1:  # Skip empty tables
                            headers = table[0] if table[0] else []
                            
                            # Look for the header pattern
                            if any('Namn' in str(h) for h in headers if h):
                                for row in table[1:]:
                                    if row and len(row) >= 6:
                                        person_data = self.parse_table_row(row, postal_code, area_name)
                                        if person_data:
                                            results.append(person_data)
                    
                    # Also try manual text parsing as fallback
                    manual_results = self.parse_text_manually(text, postal_code, area_name)
                    results.extend(manual_results)
        
        return results
    
    def extract_postal_code_from_text(self, text):
        """Extract postal code from text"""
        # Look for pattern like "167 72 Bromma"
        match = re.search(r'(\d{3}\s\d{2})\s+([A-Za-zÀ-ÿ]+)', text)
        if match:
            return match.group(1), match.group(2)
        return None, None
    
    def parse_table_row(self, row, postal_code, area_name):
        """Parse a table row"""
        try:
            if not row or len(row) < 6:
                return None
                
            # Combine all cells into a single string and parse
            row_text = ' '.join(str(cell) if cell else '' for cell in row)
            return self.parse_person_text(row_text, postal_code, area_name)
            
        except Exception as e:
            print(f"Error parsing table row: {e}")
            return None
    
    def parse_text_manually(self, text, postal_code, area_name):
        """Manual text parsing as fallback"""
        results = []
        
        # Split into lines and look for data patterns
        lines = text.split('\n')
        
        for line in lines:
            # Skip header and empty lines
            if not line.strip() or 'Namn, adress' in line or len(line.strip()) < 20:
                continue
                
            # Look for lines that contain person data
            # Pattern: name with comma, followed by numbers
            if ',' in line and re.search(r'\d{2}\s*\d{2}\s*\d+\s*[NJ]\s*\d', line):
                person_data = self.parse_person_text(line, postal_code, area_name)
                if person_data:
                    results.append(person_data)
        
        return results
    
    def parse_person_text(self, text, postal_code, area_name):
        """Parse person data from text"""
        try:
            # Clean up the text
            text = text.strip()
            
            if ',' not in text:
                return None
            
            # Split on first comma to get name
            name_part, rest = text.split(',', 1)
            name = name_part.strip()
            
            # Use regex to find all number sequences
            numbers = re.findall(r'-?\d[\d\s]*', rest)
            
            if len(numbers) < 5:
                return None
            
            # Clean numbers (remove spaces within numbers)
            clean_numbers = []
            for num in numbers:
                clean_num = re.sub(r'\s+', '', num)
                if clean_num:
                    clean_numbers.append(clean_num)
            
            if len(clean_numbers) < 5:
                return None
            
            # Find payment remarks (N or J)
            payment_match = re.search(r'\b([NJ])\b', rest)
            payment_remarks = payment_match.group(1) if payment_match else 'N'
            
            # Extract address (text between name and first number)
            address_match = re.match(r'^\s*([A-Za-zÀ-ÿ\s\d]+?)\s+\d', rest)
            address = address_match.group(1).strip() if address_match else ""
            
            # Parse numbers in expected order: age, year, rank, salary, capital
            try:
                age = int(clean_numbers[0])
                income_year = int(clean_numbers[1]) + 2000
                salary_rank = int(clean_numbers[2])
                salary = int(clean_numbers[3]) if clean_numbers[3] != '0' else 0
                capital = int(clean_numbers[4]) if len(clean_numbers) > 4 and clean_numbers[4] != '0' else 0
                
                # Validate age range
                if age < 15 or age > 100:
                    return None
                
                return {
                    'name': name,
                    'address': address,
                    'postal_code': postal_code,
                    'area_name': area_name,
                    'age': age,
                    'income_year': income_year,
                    'salary_rank': salary_rank,
                    'payment_remarks': payment_remarks == 'J',
                    'salary': salary,
                    'capital': capital
                }
                
            except (ValueError, IndexError):
                return None
                
        except Exception as e:
            return None
    
    def parse_all_pdfs(self, pdf_directory):
        """Parse all PDF files"""
        pdf_dir = Path(pdf_directory)
        all_data = []
        
        for pdf_file in pdf_dir.glob("*.pdf"):
            print(f"Parsing {pdf_file.name}...")
            try:
                data = self.extract_table_data(pdf_file)
                all_data.extend(data)
                print(f"Extracted {len(data)} records from {pdf_file.name}")
            except Exception as e:
                print(f"Error parsing {pdf_file.name}: {e}")
        
        return all_data

if __name__ == "__main__":
    parser = ImprovedRatsitParser()
    data = parser.parse_all_pdfs("pdfer")
    
    if data:
        df = pd.DataFrame(data)
        print(f"\nTotal records extracted: {len(df)}")
        print("\nSample data:")
        print(df.head())
        df.to_csv("parsed_data.csv", index=False)
    else:
        print("No data extracted")