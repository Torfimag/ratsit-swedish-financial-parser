import pdfplumber
import re
import pandas as pd
from pathlib import Path

class PositionBasedParser:
    def __init__(self):
        pass
        
    def parse_pdf(self, pdf_path):
        """Parse PDF using character positions to separate columns"""
        results = []
        
        with pdfplumber.open(pdf_path) as pdf:
            for page in pdf.pages:
                text = page.extract_text()
                if not text:
                    continue
                
                # Extract postal code and area
                postal_code, area_name = self.extract_postal_code(text)
                
                # Get character-level data with positions
                chars = page.chars
                if not chars:
                    continue
                
                # Group characters by rows and then separate into columns
                rows = self.group_chars_into_rows(chars)
                
                for row_chars in rows:
                    if not row_chars:
                        continue
                    
                    # Extract text from this row
                    row_text = ''.join([c['text'] for c in sorted(row_chars, key=lambda x: x['x0'])])
                    
                    # Skip headers and short rows
                    if len(row_text.strip()) < 40 or 'Namn, adress' in row_text or 'Å IÅ LR' in row_text:
                        continue
                    
                    # Separate the row into columns based on x-coordinates
                    columns = self.separate_into_columns(row_chars)
                    
                    # Parse each column as a separate record
                    for column_chars in columns:
                        if column_chars:
                            column_text = ''.join([c['text'] for c in sorted(column_chars, key=lambda x: x['x0'])])
                            record = self.parse_single_column(column_text.strip(), postal_code, area_name)
                            if record:
                                results.append(record)
        
        return results
    
    def group_chars_into_rows(self, chars, y_tolerance=3):
        """Group characters into rows based on y-coordinate"""
        if not chars:
            return []
        
        # Sort by y-coordinate
        sorted_chars = sorted(chars, key=lambda c: c['y0'])
        
        rows = []
        current_row = [sorted_chars[0]]
        current_y = sorted_chars[0]['y0']
        
        for char in sorted_chars[1:]:
            if abs(char['y0'] - current_y) <= y_tolerance:
                current_row.append(char)
            else:
                rows.append(current_row)
                current_row = [char]
                current_y = char['y0']
        
        if current_row:
            rows.append(current_row)
        
        return rows
    
    def separate_into_columns(self, row_chars, num_columns=3):
        """Separate a row of characters into columns based on x-coordinates"""
        if not row_chars:
            return []
        
        # Sort by x-coordinate
        sorted_chars = sorted(row_chars, key=lambda c: c['x0'])
        
        # Find column boundaries by looking for gaps in x-coordinates
        x_positions = [c['x0'] for c in sorted_chars]
        min_x, max_x = min(x_positions), max(x_positions)
        
        # Divide into approximately equal columns
        column_width = (max_x - min_x) / num_columns
        
        columns = [[] for _ in range(num_columns)]
        
        for char in sorted_chars:
            column_index = min(int((char['x0'] - min_x) / column_width), num_columns - 1)
            columns[column_index].append(char)
        
        # Filter out empty columns and ensure meaningful content
        meaningful_columns = []
        for column in columns:
            if column:
                text = ''.join([c['text'] for c in sorted(column, key=lambda x: x['x0'])])
                # Must contain a name pattern (letters followed by comma)
                if re.search(r'[A-Za-zÀ-ÿ]+.*,', text):
                    meaningful_columns.append(column)
        
        return meaningful_columns
    
    def extract_postal_code(self, text):
        """Extract postal code from text"""
        lines = text.split('\n')
        for line in lines:
            match = re.search(r'(\d{3}\s\d{2})\s+([A-Za-zÀ-ÿ]+)', line)
            if match:
                return match.group(1), match.group(2)
        return None, None
    
    def parse_single_column(self, text, postal_code, area_name):
        """Parse a single column of text as one person record"""
        try:
            if not text or ',' not in text:
                return None
            
            # Clean the text
            text = re.sub(r'\s+', ' ', text.strip())
            
            # Split name from rest
            if ',' not in text:
                return None
                
            name_part, rest = text.split(',', 1)
            name = name_part.strip()
            
            if not name or len(name) < 2:
                return None
            
            # Parse the rest: Address Age Year Rank N/J Salary Capital
            rest = rest.strip()
            
            # Use regex to carefully extract the components
            # Pattern: Address (letters/numbers/spaces) followed by Age(2digits) Year(2digits) Rank(digits) N/J Salary Capital
            pattern = r'^(.+?)\s+(\d{2})\s+(\d{2})\s+(\d+)\s+([NJ])\s+([\d\s\-]+?)(?:\s+([\d\s\-]+))?$'
            match = re.match(pattern, rest)
            
            if not match:
                return None
            
            address = match.group(1).strip()
            age = int(match.group(2))
            year = int(match.group(3))
            rank = int(match.group(4))
            payment = match.group(5)
            salary_str = match.group(6).strip()
            capital_str = match.group(7).strip() if match.group(7) else '0'
            
            # Validate age
            if age < 15 or age > 100:
                return None
            
            # Convert year
            income_year = year + 2000 if year < 50 else year + 1900
            
            # Parse salary and capital amounts - remove spaces within numbers
            salary = self.parse_amount(salary_str)
            capital = self.parse_amount(capital_str)
            
            # Sanity check on salary (reasonable range)
            if salary > 100_000_000:  # 100 million SEK seems unreasonable
                return None
            
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
            
        except (ValueError, AttributeError) as e:
            return None
    
    def parse_amount(self, amount_str):
        """Parse amount string with space-separated thousands"""
        if not amount_str:
            return 0
        
        # Handle negative amounts
        is_negative = amount_str.startswith('-')
        if is_negative:
            amount_str = amount_str[1:]
        
        # Remove extra spaces and join digits
        # For Swedish format like "932 500", this becomes "932500"
        parts = amount_str.split()
        if len(parts) <= 3:  # Reasonable number of parts for an amount
            clean_str = ''.join(parts)
            try:
                value = int(clean_str) if clean_str != '0' else 0
                return -value if is_negative else value
            except ValueError:
                return 0
        
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
    parser = PositionBasedParser()
    data = parser.parse_all_pdfs("pdfer")
    
    if data:
        df = pd.DataFrame(data)
        print(f"\nTotal records extracted: {len(df)}")
        
        # Filter out unrealistic salaries for analysis
        reasonable_data = df[df['salary'] < 50_000_000]  # Under 50M SEK
        print(f"Records with reasonable salaries: {len(reasonable_data)}")
        
        print("\nSample data:")
        print(reasonable_data[['name', 'area_name', 'age', 'salary', 'capital']].head(10))
        
        if len(reasonable_data) > 0:
            print(f"\nSalary statistics (reasonable range):")
            print(f"Average: {reasonable_data['salary'].mean():,.0f} SEK")
            print(f"Median: {reasonable_data['salary'].median():,.0f} SEK")
            print(f"Max: {reasonable_data['salary'].max():,.0f} SEK")
        
        df.to_csv("position_parsed_data.csv", index=False)
        print("\nData saved to position_parsed_data.csv")
    else:
        print("No data extracted")