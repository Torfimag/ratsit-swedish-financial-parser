import pdfplumber
import re
import pandas as pd
from pathlib import Path

class PatternBasedParser:
    def __init__(self):
        pass
        
    def parse_pdf(self, pdf_path):
        """Parse PDF using known patterns from Ratsit data"""
        results = []
        
        with pdfplumber.open(pdf_path) as pdf:
            for page in pdf.pages:
                text = page.extract_text()
                if not text:
                    continue
                
                # Extract postal code and area
                postal_code, area_name = self.extract_postal_code(text)
                
                # Process each line looking for data patterns
                lines = text.split('\n')
                for line in lines:
                    if self.looks_like_data_line(line):
                        # Try to extract records from this line
                        records = self.extract_records_from_line(line, postal_code, area_name)
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
    
    def looks_like_data_line(self, line):
        """Check if line contains person data"""
        # Must be long enough and contain names with commas
        if len(line.strip()) < 50:
            return False
        
        # Skip headers
        if 'Namn, adress' in line or 'Å IÅ LR' in line or 'Prova' in line:
            return False
        
        # Must contain at least one name pattern and numbers
        if re.search(r'[A-Za-zÀ-ÿ]+.*,.*\d+.*[NJ]', line):
            return True
        
        return False
    
    def extract_records_from_line(self, line, postal_code, area_name):
        """Extract multiple records from a single line (multi-column)"""
        records = []
        
        # Strategy: Look for the pattern "Name, Address" followed by numbers and N/J
        # Then try to identify where each record ends and the next begins
        
        # Find all potential name starts
        name_pattern = r'([A-Za-zÀ-ÿ\s\-\']+),\s*([A-Za-zÀ-ÿ\d\s\-\']*?)'
        name_matches = list(re.finditer(name_pattern, line))
        
        if not name_matches:
            return records
        
        # For each name match, try to extract a complete record
        for i, match in enumerate(name_matches):
            start_pos = match.start()
            
            # Determine where this record ends (start of next name or end of line)
            if i + 1 < len(name_matches):
                end_pos = name_matches[i + 1].start()
            else:
                end_pos = len(line)
            
            record_text = line[start_pos:end_pos].strip()
            
            # Parse this individual record
            record = self.parse_individual_record(record_text, postal_code, area_name)
            if record:
                records.append(record)
        
        return records
    
    def parse_individual_record(self, text, postal_code, area_name):
        """Parse a single record from text"""
        try:
            # Expected format: "Name, Address Age Year Rank N/J Salary Capital"
            if ',' not in text:
                return None
            
            name_part, rest = text.split(',', 1)
            name = name_part.strip()
            
            if not name or len(name) < 3:
                return None
            
            # Extract all numbers from the rest
            all_numbers = re.findall(r'-?\d+', rest)
            
            if len(all_numbers) < 5:  # Need at least age, year, rank, salary, capital
                return None
            
            # Find the N/J marker
            payment_match = re.search(r'\b([NJ])\b', rest)
            payment = payment_match.group(1) if payment_match else 'N'
            
            # Extract address (text before first number)
            address_match = re.match(r'^\s*([A-Za-zÀ-ÿ\d\s\-\',\.]+?)\s+\d', rest)
            address = address_match.group(1).strip() if address_match else ''
            
            # Parse the key fields
            # Typically: Age (2 digits), Year (2 digits), Rank, then salary/capital amounts
            
            # Find reasonable age (15-100)
            age = None
            year = None
            age_year_idx = -1
            
            for i, num in enumerate(all_numbers):
                num_val = int(num)
                if 15 <= num_val <= 100:  # Potential age
                    if i + 1 < len(all_numbers):
                        next_num = int(all_numbers[i + 1])
                        if 20 <= next_num <= 30:  # Year like 22, 23 (for 2022, 2023)
                            age = num_val
                            year = next_num
                            age_year_idx = i
                            break
            
            if age is None or year is None:
                return None
            
            # Rank should be the next number after year
            rank = 0
            if age_year_idx + 2 < len(all_numbers):
                rank = int(all_numbers[age_year_idx + 2])
            
            # Salary and capital are typically the largest remaining numbers
            remaining_numbers = [int(n) for n in all_numbers[age_year_idx + 3:]]
            
            salary = 0
            capital = 0
            
            if remaining_numbers:
                # Find the largest positive number as salary
                positive_nums = [n for n in remaining_numbers if n > 0]
                if positive_nums:
                    salary = max(positive_nums)
                
                # Capital might be negative or smaller
                other_nums = [n for n in remaining_numbers if n != salary]
                if other_nums:
                    capital = other_nums[0]  # Take first remaining number
            
            # Sanity checks
            if salary > 50_000_000:  # Too high
                salary = 0
            
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
    
    def parse_all_pdfs(self, pdf_directory):
        """Parse all PDF files"""
        pdf_dir = Path(pdf_directory)
        all_data = []
        
        for pdf_file in pdf_dir.glob("*.pdf"):
            print(f"Parsing {pdf_file.name}...")
            try:
                data = self.parse_pdf(pdf_file)
                # Filter out records with unreasonable salaries
                filtered_data = [r for r in data if r['salary'] < 20_000_000]
                all_data.extend(filtered_data)
                print(f"Extracted {len(filtered_data)} valid records from {pdf_file.name}")
            except Exception as e:
                print(f"Error parsing {pdf_file.name}: {e}")
        
        return all_data

# Test the parser
if __name__ == "__main__":
    parser = PatternBasedParser()
    data = parser.parse_all_pdfs("pdfer")
    
    if data:
        df = pd.DataFrame(data)
        print(f"\nTotal records extracted: {len(df)}")
        
        # Show sample data
        print("\nSample data:")
        print(df[['name', 'area_name', 'age', 'salary', 'capital']].head(10))
        
        # Show statistics for non-zero salaries
        salary_data = df[df['salary'] > 0]
        if len(salary_data) > 0:
            print(f"\nSalary statistics ({len(salary_data)} records with salary > 0):")
            print(f"Average: {salary_data['salary'].mean():,.0f} SEK")
            print(f"Median: {salary_data['salary'].median():,.0f} SEK")
            print(f"Max: {salary_data['salary'].max():,.0f} SEK")
            print(f"Min: {salary_data['salary'].min():,.0f} SEK")
        
        # Show area distribution
        print("\nRecords by area:")
        print(df['area_name'].value_counts())
        
        df.to_csv("pattern_parsed_data.csv", index=False)
        print("\nData saved to pattern_parsed_data.csv")
        
        # Update database with new data
        print("\nUpdating database with parsed data...")
        from database import RatsitDatabase
        db = RatsitDatabase()
        db.insert_persons(data)
        print("Database updated!")
        
    else:
        print("No data extracted")