import pdfplumber
import re
import pandas as pd
from pathlib import Path

class SmartRatsitParser:
    def __init__(self):
        pass
        
    def parse_pdf(self, pdf_path):
        """Parse PDF by handling multi-column layout"""
        results = []
        
        with pdfplumber.open(pdf_path) as pdf:
            for page in pdf.pages:
                text = page.extract_text()
                if not text:
                    continue
                
                # Extract postal code and area
                postal_code, area_name = self.extract_postal_code(text)
                
                # Process each line
                lines = text.split('\n')
                for line in lines:
                    # Skip headers and short lines
                    if len(line.strip()) < 50 or 'Namn, adress' in line:
                        continue
                    
                    # Parse multi-column line
                    records = self.parse_multi_column_line(line, postal_code, area_name)
                    results.extend(records)
        
        return results
    
    def extract_postal_code(self, text):
        """Extract postal code from text"""
        lines = text.split('\n')
        for line in lines:
            match = re.search(r'(\d{3}\s\d{2})\s+([A-Za-zÀ-ÿ]+)', line)
            if match:
                return match.group(1), match.group(2)
        return None, None
    
    def parse_multi_column_line(self, line, postal_code, area_name):
        """Parse a line that contains multiple records from different columns"""
        records = []
        
        # Look for pattern: Name, Address followed by numbers
        # Use regex to find all instances of "Name, Address" pattern
        pattern = r'([A-Za-zÀ-ÿ\s\-\'\.]+),\s+([A-Za-zÀ-ÿ\d\s\-\'\.]*?)\s+(\d{2})(\d{2})\s+(\d+)\s+([NJ])\s+([\d\s\-]+)(?:\s+([\d\s\-]+))?'
        
        # Find all matches in the line
        matches = re.finditer(pattern, line)
        
        for match in matches:
            try:
                name = match.group(1).strip()
                address = match.group(2).strip()
                age = int(match.group(3))
                year = int(match.group(4))
                rank = int(match.group(5))
                payment = match.group(6)
                salary_str = match.group(7)
                capital_str = match.group(8) if match.group(8) else '0'
                
                # Validate age range
                if age < 15 or age > 100:
                    continue
                
                # Convert year
                income_year = year + 2000 if year < 50 else year + 1900
                
                # Clean and parse amounts
                salary = self.parse_amount(salary_str)
                capital = self.parse_amount(capital_str)
                
                if name and len(name) > 2:  # Valid name
                    records.append({
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
                    })
                    
            except (ValueError, AttributeError):
                continue
        
        # If regex didn't work, try simpler splitting approach
        if not records:
            records = self.parse_by_splitting(line, postal_code, area_name)
        
        return records
    
    def parse_by_splitting(self, line, postal_code, area_name):
        """Alternative parsing by looking for name patterns and splitting"""
        records = []
        
        # Find all name patterns (Lastname Firstname, or Firstname Lastname,)
        name_matches = list(re.finditer(r'([A-Za-zÀ-ÿ\s\-\']+),', line))
        
        if len(name_matches) >= 2:  # At least 2 names = multiple columns
            
            # Split the line based on name positions
            splits = []
            for i, match in enumerate(name_matches):
                start = match.start()
                end = name_matches[i + 1].start() if i + 1 < len(name_matches) else len(line)
                segment = line[start:end].strip()
                
                if segment:
                    splits.append(segment)
            
            # Also add the last segment if there's remaining text
            if name_matches:
                last_segment = line[name_matches[-1].end():].strip()
                if last_segment and len(last_segment) > 20:  # Has substantial content
                    splits[-1] += ' ' + last_segment
            
            # Parse each segment
            for segment in splits:
                record = self.parse_single_record(segment, postal_code, area_name)
                if record:
                    records.append(record)
        
        return records
    
    def parse_single_record(self, text, postal_code, area_name):
        """Parse a single person record"""
        try:
            if ',' not in text:
                return None
            
            # Split name from rest
            name_part, rest = text.split(',', 1)
            name = name_part.strip()
            
            if not name or len(name) < 2:
                return None
            
            # Extract numbers from the rest
            numbers = re.findall(r'-?\d+', rest)
            
            if len(numbers) < 5:
                return None
            
            # Find payment remarks
            payment_match = re.search(r'\b([NJ])\b', rest)
            payment = payment_match.group(1) if payment_match else 'N'
            
            # Extract address (text before first number)
            address_match = re.match(r'^\s*([A-Za-zÀ-ÿ\d\s\-\'\.]+?)\s+\d', rest)
            address = address_match.group(1).strip() if address_match else ''
            
            # Parse the key numbers - typically: age, year, rank, then salary/capital amounts
            age = int(numbers[0])
            year = int(numbers[1])
            rank = int(numbers[2])
            
            # Validate age
            if age < 15 or age > 100:
                return None
            
            # Find the salary and capital amounts (usually the larger numbers)
            salary_capital_nums = [int(n) for n in numbers[3:]]
            
            salary = 0
            capital = 0
            
            if len(salary_capital_nums) >= 2:
                # Usually salary is larger, capital might be negative
                salary = salary_capital_nums[0]
                capital = salary_capital_nums[1]
            elif len(salary_capital_nums) >= 1:
                salary = salary_capital_nums[0]
            
            income_year = year + 2000 if year < 50 else year + 1900
            
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
            
        except (ValueError, IndexError):
            return None
    
    def parse_amount(self, amount_str):
        """Parse amount string, handling spaces and negatives"""
        if not amount_str:
            return 0
        
        # Remove spaces and handle negatives
        clean_str = amount_str.replace(' ', '').replace(',', '')
        
        try:
            return int(clean_str) if clean_str not in ['0', '—', ''] else 0
        except ValueError:
            return 0
    
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

if __name__ == "__main__":
    parser = SmartRatsitParser()
    data = parser.parse_all_pdfs("pdfer")
    
    if data:
        df = pd.DataFrame(data)
        print(f"\nTotal records extracted: {len(df)}")
        print("\nSample data:")
        print(df[['name', 'area_name', 'age', 'salary', 'capital']].head(10))
        
        # Show salary distribution
        print(f"\nSalary statistics:")
        print(f"Average: {df['salary'].mean():,.0f} SEK")
        print(f"Median: {df['salary'].median():,.0f} SEK")
        print(f"Max: {df['salary'].max():,.0f} SEK")
        
        df.to_csv("smart_parsed_data.csv", index=False)
        print("\nData saved to smart_parsed_data.csv")
    else:
        print("No data extracted")