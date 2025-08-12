import pdfplumber
import re
import pandas as pd
from pathlib import Path

class FinalRatsitParser:
    def __init__(self):
        pass
        
    def parse_pdf(self, pdf_path):
        """Parse a single PDF using character-level positioning"""
        results = []
        
        with pdfplumber.open(pdf_path) as pdf:
            for page in pdf.pages:
                # Get postal code from text first
                text = page.extract_text()
                postal_code, area_name = self.extract_postal_code_from_text(text)
                
                # Extract characters with positions
                chars = page.chars
                
                # Group characters by line (similar y-coordinates)
                lines = self.group_chars_by_line(chars)
                
                # Process each line
                for line_chars in lines:
                    line_text = ''.join([c['text'] for c in line_chars])
                    
                    # Check if this looks like a data line
                    if self.is_data_line(line_text):
                        person_data = self.parse_data_line_with_positions(line_chars, postal_code, area_name)
                        if person_data:
                            results.append(person_data)
        
        return results
    
    def group_chars_by_line(self, chars, y_tolerance=3):
        """Group characters by line based on y-coordinate"""
        if not chars:
            return []
            
        # Sort by y-coordinate (top to bottom)
        sorted_chars = sorted(chars, key=lambda c: c['y0'])
        
        lines = []
        current_line = [sorted_chars[0]]
        current_y = sorted_chars[0]['y0']
        
        for char in sorted_chars[1:]:
            if abs(char['y0'] - current_y) <= y_tolerance:
                current_line.append(char)
            else:
                # Sort current line by x-coordinate (left to right)
                current_line.sort(key=lambda c: c['x0'])
                lines.append(current_line)
                current_line = [char]
                current_y = char['y0']
        
        # Don't forget the last line
        if current_line:
            current_line.sort(key=lambda c: c['x0'])
            lines.append(current_line)
        
        return lines
    
    def extract_postal_code_from_text(self, text):
        """Extract postal code from text"""
        lines = text.split('\n')
        for line in lines:
            match = re.search(r'(\d{3}\s\d{2})\s+([A-Za-zÀ-ÿ]+)', line)
            if match:
                return match.group(1), match.group(2)
        return None, None
    
    def is_data_line(self, line_text):
        """Check if this is a person data line"""
        if len(line_text.strip()) < 30:
            return False
            
        if 'Namn, adress' in line_text or 'Å IÅ LR' in line_text:
            return False
            
        # Look for pattern: Name, Address followed by numbers and N/J
        if ',' in line_text and re.search(r'[A-Za-zÀ-ÿ]+.*\d.*[NJ]', line_text):
            return True
            
        return False
    
    def parse_data_line_with_positions(self, line_chars, postal_code, area_name):
        """Parse a data line using character positions for better accuracy"""
        try:
            line_text = ''.join([c['text'] for c in line_chars])
            
            # Use simple text parsing first
            return self.parse_simple_line(line_text, postal_code, area_name)
            
        except Exception as e:
            return None
    
    def parse_simple_line(self, line_text, postal_code, area_name):
        """Simple line parsing with better regex"""
        try:
            # Pattern: Name, Address Age Year Rank N/J Salary Capital
            # Example: "Kindström Magnus, Djupdalsvägen 114 53 23 80 N 932 500 -129 720"
            
            if ',' not in line_text:
                return None
            
            # Split name from rest
            name_part, rest = line_text.split(',', 1)
            name = name_part.strip()
            
            if not name:
                return None
            
            # Find all sequences that look like our data pattern
            # Look for: address followed by 2-3 digits (age), 2 digits (year), numbers, N/J, large numbers
            pattern = r'^\s*(.+?)\s+(\d{2})\s+(\d{2})\s+(\d+)\s+([NJ])\s+([\d\s-]+)(?:\s+([\d\s-]+))?'
            match = re.search(pattern, rest)
            
            if not match:
                return None
            
            address = match.group(1).strip()
            age = int(match.group(2))
            year = int(match.group(3))
            rank = int(match.group(4))
            payment = match.group(5)
            salary_str = match.group(6).replace(' ', '').replace(',', '')
            capital_str = match.group(7).replace(' ', '').replace(',', '') if match.group(7) else '0'
            
            # Validate age
            if age < 15 or age > 100:
                return None
            
            # Convert year
            income_year = year + 2000 if year < 50 else year + 1900
            
            # Parse amounts
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
                'salary_rank': rank,
                'payment_remarks': payment == 'J',
                'salary': salary,
                'capital': capital
            }
            
        except Exception:
            return None
    
    def parse_all_pdfs(self, pdf_directory):
        """Parse all PDF files"""
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

# Update main.py to use the new parser
if __name__ == "__main__":
    parser = FinalRatsitParser()
    data = parser.parse_all_pdfs("pdfer")
    
    if data:
        df = pd.DataFrame(data)
        print(f"\nTotal records extracted: {len(df)}")
        print("\nSample data:")
        print(df[['name', 'area_name', 'age', 'salary', 'capital']].head(10))
        df.to_csv("final_parsed_data.csv", index=False)
    else:
        print("No data extracted")