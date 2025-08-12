import pdfplumber
import re
import pandas as pd
from pathlib import Path

class PreciseRatsitParser:
    def __init__(self):
        pass
        
    def parse_pdf(self, pdf_path):
        """Parse PDF with precise Ratsit format handling"""
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
                    if self.is_data_line(line):
                        # Parse this multi-column line
                        records = self.parse_multi_column_line(line, postal_code, area_name)
                        results.extend(records)
        
        return results
    
    def extract_postal_code(self, text):
        """Extract postal code from text"""
        lines = text.split('\n')
        for line in lines:
            # Look for pattern like "167 72 Bromma"
            match = re.search(r'(\d{3}\s\d{2})\s+([A-Za-zÀ-ÿ]+)', line)
            if match:
                return match.group(1), match.group(2)
        return None, None
    
    def is_data_line(self, line):
        """Check if line contains person data"""
        # Must be substantial length
        if len(line.strip()) < 50:
            return False
            
        # Skip headers
        if any(skip in line for skip in ['Namn, adress', 'Å IÅ LR', 'Prova', 'ratsit']):
            return False
        
        # Must contain names and numbers pattern
        if re.search(r'[A-Za-zÀ-ÿ]+.*,.*\d.*[NJ]', line):
            return True
        
        return False
    
    def parse_multi_column_line(self, line, postal_code, area_name):
        """Parse line with multiple records (3-column layout)"""
        records = []
        
        # Strategy: The key insight is that each record follows the pattern:
        # "Name, Address Age(2digits) Year(2digits) Rank(1-3digits) N/J Salary Capital"
        
        # Find all instances where we have "Name, " followed by data
        pattern = r'([A-Za-zÀ-ÿ\s\-\'\.]+),\s*([^,]*?)(\d{2})(\d{2})\s+(\d+)\s+([NJ])\s+([\d\s\-]+?)(?=(?:[A-Za-zÀ-ÿ]+,)|(?:\s+[\d\s\-]+\s*$))'
        
        matches = list(re.finditer(pattern, line))
        
        for i, match in enumerate(matches):
            try:
                name = match.group(1).strip()
                address_part = match.group(2).strip()
                age = int(match.group(3))
                year = int(match.group(4))
                rank = int(match.group(5))
                payment = match.group(6)
                amounts_str = match.group(7)
                
                # Validate age
                if age < 15 or age > 100:
                    continue
                
                # Parse the amounts string - this contains salary and capital
                salary, capital = self.parse_amounts(amounts_str)
                
                # Income year
                income_year = year + 2000 if year < 50 else year + 1900
                
                # Clean up address
                address = self.clean_address(address_part)
                
                if name and len(name) > 2:
                    record = {
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
                    records.append(record)
                    
            except (ValueError, AttributeError):
                continue
        
        # If regex approach didn't work well, try split approach
        if len(records) == 0:
            records = self.parse_by_splitting(line, postal_code, area_name)
        
        return records
    
    def parse_amounts(self, amounts_str):
        """Parse salary and capital from amounts string"""
        # Clean and split the amounts string
        # Format like "630 000 275 896" or "932 500 -129 720"
        amounts_str = amounts_str.strip()
        
        # Find all number sequences (including negative)
        number_parts = re.findall(r'-?\d+(?:\s+\d+)*', amounts_str)
        
        salary = 0
        capital = 0
        
        if len(number_parts) >= 2:
            # First number sequence is salary, second is capital
            salary_str = number_parts[0].replace(' ', '')
            capital_str = number_parts[1].replace(' ', '')
            
            try:
                salary = int(salary_str) if salary_str != '0' else 0
            except ValueError:
                salary = 0
                
            try:
                capital = int(capital_str) if capital_str != '0' else 0
            except ValueError:
                capital = 0
                
        elif len(number_parts) == 1:
            # Only one number - treat as salary
            salary_str = number_parts[0].replace(' ', '')
            try:
                salary = int(salary_str) if salary_str != '0' else 0
            except ValueError:
                salary = 0
        
        # Sanity check - very large numbers are likely parsing errors
        if salary > 50_000_000:
            salary = 0
        if abs(capital) > 10_000_000:
            capital = 0
            
        return salary, capital
    
    def clean_address(self, address_part):
        """Clean up extracted address"""
        # Remove any trailing numbers that might be age/year/rank
        address = re.sub(r'\s+\d+$', '', address_part).strip()
        return address
    
    def parse_by_splitting(self, line, postal_code, area_name):
        """Alternative parsing method using name positions"""
        records = []
        
        # Find all name positions
        name_positions = []
        for match in re.finditer(r'([A-Za-zÀ-ÿ\s\-\'\.]+),', line):
            name_positions.append((match.start(), match.end(), match.group(1).strip()))
        
        if len(name_positions) < 2:
            return records
        
        # Process each name segment
        for i, (start, end, name) in enumerate(name_positions):
            try:
                # Determine the segment boundaries
                if i + 1 < len(name_positions):
                    segment_end = name_positions[i + 1][0]
                else:
                    segment_end = len(line)
                
                segment = line[end:segment_end].strip()
                
                # Parse this segment
                record = self.parse_single_segment(name, segment, postal_code, area_name)
                if record:
                    records.append(record)
                    
            except Exception:
                continue
        
        return records
    
    def parse_single_segment(self, name, segment, postal_code, area_name):
        """Parse a single person segment"""
        try:
            # Extract numbers from segment
            numbers = re.findall(r'-?\d+', segment)
            
            if len(numbers) < 5:
                return None
            
            # Find N/J marker
            payment_match = re.search(r'\b([NJ])\b', segment)
            payment = payment_match.group(1) if payment_match else 'N'
            
            # Extract address (text before first number)
            address_match = re.match(r'^([A-Za-zÀ-ÿ\d\s\-\'\.]*?)\s*\d', segment)
            address = address_match.group(1).strip() if address_match else ''
            
            # Parse the numbers - look for age pattern (15-100)
            age_idx = -1
            for i, num_str in enumerate(numbers):
                num = int(num_str)
                if 15 <= num <= 100 and i + 1 < len(numbers):
                    next_num = int(numbers[i + 1])
                    if 20 <= next_num <= 30:  # Year like 22, 23
                        age_idx = i
                        break
            
            if age_idx == -1:
                return None
            
            age = int(numbers[age_idx])
            year = int(numbers[age_idx + 1])
            income_year = year + 2000 if year < 50 else year + 1900
            
            # Rank is usually next
            rank = int(numbers[age_idx + 2]) if age_idx + 2 < len(numbers) else 0
            
            # Remaining numbers are salary/capital
            remaining_nums = numbers[age_idx + 3:]
            salary, capital = 0, 0
            
            if len(remaining_nums) >= 2:
                # Combine space-separated parts for Swedish number format
                # Look for the pattern where we have parts that form larger numbers
                salary_parts = []
                capital_parts = []
                
                # Simple approach: take first large number as salary, last as capital
                for num_str in remaining_nums:
                    num = int(num_str)
                    if abs(num) > 1000 and salary == 0:
                        salary = abs(num)
                    elif capital == 0:
                        capital = num
            
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
                # Filter reasonable salaries
                filtered_data = [r for r in data if 0 <= r['salary'] <= 20_000_000]
                all_data.extend(filtered_data)
                print(f"Extracted {len(filtered_data)} valid records from {pdf_file.name}")
                
                # Show sample for debugging
                if filtered_data:
                    sample = filtered_data[0]
                    print(f"  Sample: {sample['name']} - {sample['salary']:,} SEK")
                    
            except Exception as e:
                print(f"Error parsing {pdf_file.name}: {e}")
        
        return all_data

if __name__ == "__main__":
    parser = PreciseRatsitParser()
    data = parser.parse_all_pdfs("pdfer")
    
    if data:
        df = pd.DataFrame(data)
        print(f"\nTotal records extracted: {len(df)}")
        
        # Show salary statistics
        salary_data = df[df['salary'] > 0]
        if len(salary_data) > 0:
            print(f"\nRecords with salary > 0: {len(salary_data)}")
            print(f"Average salary: {salary_data['salary'].mean():,.0f} SEK")
            print(f"Median salary: {salary_data['salary'].median():,.0f} SEK")
            print(f"Max salary: {salary_data['salary'].max():,.0f} SEK")
        
        # Show top earners
        top_earners = df.nlargest(10, 'salary')
        print("\nTop 10 earners:")
        for _, row in top_earners.iterrows():
            print(f"{row['name']:<25} {row['area_name']:<12} {row['salary']:8,} SEK")
        
        # Update database
        print("\nUpdating database with parsed data...")
        from database import RatsitDatabase
        db = RatsitDatabase()
        db.insert_persons(data)
        print("Database updated with real parsed data!")
        
        df.to_csv("precise_parsed_data.csv", index=False)
        
    else:
        print("No data extracted")