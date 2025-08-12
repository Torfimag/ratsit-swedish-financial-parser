import pdfplumber
import re
import pandas as pd
from pathlib import Path

class FinalWorkingParser:
    def __init__(self):
        pass
        
    def parse_pdf(self, pdf_path):
        """Parse PDF with correct Swedish number format handling"""
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
            match = re.search(r'(\d{3}\s\d{2})\s+([A-Za-zÀ-ÿ]+)', line)
            if match:
                return match.group(1), match.group(2)
        return None, None
    
    def is_data_line(self, line):
        """Check if line contains person data"""
        if len(line.strip()) < 50:
            return False
        if any(skip in line for skip in ['Namn, adress', 'Å IÅ LR', 'Prova', 'ratsit']):
            return False
        if re.search(r'[A-Za-zÀ-ÿ]+.*,.*\d.*[NJ]', line):
            return True
        return False
    
    def parse_multi_column_line(self, line, postal_code, area_name):
        """Parse line with multiple records using improved amount parsing"""
        records = []
        
        # Split the line at each "N " or "J " to separate individual records
        parts = re.split(r'\b([NJ])\s+', line)
        
        if len(parts) < 3:
            return records
        
        # Process each record (parts come in groups of 3: before_payment, payment_marker, after_payment)
        i = 0
        while i + 2 < len(parts):
            before_payment = parts[i]
            payment_marker = parts[i + 1] if i + 1 < len(parts) else 'N'
            after_payment = parts[i + 2] if i + 2 < len(parts) else ''
            
            # Parse this individual record
            record = self.parse_individual_record(before_payment, payment_marker, after_payment, postal_code, area_name)
            if record:
                records.append(record)
            
            i += 2  # Move to next record (skip the payment marker)
        
        return records
    
    def parse_individual_record(self, before_payment, payment_marker, after_payment, postal_code, area_name):
        """Parse a single record with correct amount handling"""
        try:
            # Extract name (should be at the beginning)
            name_match = re.match(r'^.*?([A-Za-zÀ-ÿ\s\-\'\.]+),\s*(.*)$', before_payment.strip())
            if not name_match:
                return None
            
            name = name_match.group(1).strip()
            rest = name_match.group(2).strip()
            
            if not name or len(name) < 3:
                return None
            
            # Extract age, year, rank from the end of the rest string
            # Pattern: Address [Age Year Rank] - age and year are 2 digits each
            age_year_rank_match = re.search(r'(\d{2})(\d{2})\s+(\d+)\s*$', rest)
            if not age_year_rank_match:
                return None
            
            age = int(age_year_rank_match.group(1))
            year = int(age_year_rank_match.group(2))
            rank = int(age_year_rank_match.group(3))
            
            # Validate age
            if age < 15 or age > 100:
                return None
            
            # Extract address (everything before age/year/rank)
            address = rest[:age_year_rank_match.start()].strip()
            
            # Income year
            income_year = year + 2000 if year < 50 else year + 1900
            
            # Parse amounts from after_payment
            salary, capital = self.parse_swedish_amounts(after_payment)
            
            return {
                'name': name,
                'address': address,
                'postal_code': postal_code,
                'area_name': area_name,
                'age': age,
                'income_year': income_year,
                'salary_rank': rank,
                'payment_remarks': payment_marker == 'J',
                'salary': salary,
                'capital': capital
            }
            
        except (ValueError, AttributeError):
            return None
    
    def parse_swedish_amounts(self, amounts_text):
        """Parse Swedish-formatted amounts correctly"""
        if not amounts_text.strip():
            return 0, 0
        
        # Clean the text - remove any names that might follow
        amounts_text = re.sub(r'[A-Za-zÀ-ÿ]+,.*$', '', amounts_text).strip()
        
        # Find all number patterns in Swedish format
        # Pattern: optional minus, digits, optional space+digits groups
        number_pattern = r'-?\d+(?:\s+\d+)*'
        potential_numbers = re.findall(number_pattern, amounts_text)
        
        if not potential_numbers:
            return 0, 0
        
        salary = 0
        capital = 0
        
        if len(potential_numbers) >= 2:
            # Special case: if first number is "0", treat it as zero salary
            if potential_numbers[0].strip() == '0':
                salary = 0
                # All remaining parts form the capital amount
                capital_parts = potential_numbers[1:]
                capital_str = ' '.join(capital_parts)
                capital = self.swedish_number_to_int(capital_str)
            else:
                # Two amounts: salary and capital
                salary = self.swedish_number_to_int(potential_numbers[0])
                capital = self.swedish_number_to_int(potential_numbers[1])
            
        elif len(potential_numbers) == 1:
            # Only one amount - check if it looks like it contains both salary and capital
            single_amount = potential_numbers[0]
            
            # Try to split by looking for typical patterns
            # Swedish amounts are typically 3-7 digits with spaces
            parts = single_amount.split()
            
            if len(parts) >= 2:
                # Strategy: Find the natural break between salary and capital
                # Look for negative numbers first (capital is often negative)
                negative_match = re.search(r'-\d', single_amount)
                
                if negative_match:
                    # Split at the negative number
                    split_pos = negative_match.start()
                    salary_part = single_amount[:split_pos].strip()
                    capital_part = single_amount[split_pos:].strip()
                    
                    salary = self.swedish_number_to_int(salary_part) if salary_part else 0
                    capital = self.swedish_number_to_int(capital_part) if capital_part else 0
                    
                else:
                    # No negative number - need to split positive amounts intelligently
                    # Swedish salary amounts are typically:
                    # - 1-3 digits groups (like "40 500" or "1 055 700")  
                    # - Capital is usually smaller, often 1-2 digit groups (like "577" or "82 556")
                    
                    # Strategy: Try different split points and pick the most reasonable
                    possible_splits = []
                    
                    # Try splitting after 1, 2, 3, 4 digit groups
                    for split_point in [1, 2, 3, 4]:
                        if split_point < len(parts):
                            salary_part = ' '.join(parts[:split_point])
                            capital_part = ' '.join(parts[split_point:])
                            
                            salary_val = self.swedish_number_to_int(salary_part)
                            capital_val = self.swedish_number_to_int(capital_part)
                            
                            # Swedish salaries typically 100k-2M SEK, but 0 is also valid (unemployed/students)
                            salary_reasonable = (salary_val == 0) or (10_000 <= salary_val <= 5_000_000)
                            capital_reasonable = abs(capital_val) <= 50_000_000
                            
                            if salary_reasonable and capital_reasonable:
                                # Check if this forms a valid Swedish number pattern
                                salary_valid_pattern = self.is_valid_swedish_number_pattern(salary_part)
                                capital_valid_pattern = self.is_valid_swedish_number_pattern(capital_part)
                                
                                # Only consider splits that form valid Swedish number patterns
                                if salary_valid_pattern and capital_valid_pattern:
                                    # Score based on how reasonable the salary range is
                                    salary_score = 0.1  # Default low score
                                    
                                    # Special case: zero salary is valid (unemployed, students, etc.)
                                    if salary_val == 0:
                                        salary_score = 0.95  # High score - zero salary is legitimate
                                    # Prefer typical Swedish salary ranges  
                                    elif 100_000 <= salary_val <= 800_000:  # Very typical range
                                        salary_score = 1.0
                                    elif 50_000 <= salary_val <= 100_000:  # Lower but reasonable
                                        salary_score = 0.8
                                    elif 800_000 <= salary_val <= 2_000_000:  # High but reasonable
                                        salary_score = 0.6
                                    elif salary_val > 2_000_000:  # Very high salary - less likely
                                        salary_score = 0.2
                                    elif 15_000 <= salary_val < 50_000:  # Low but valid (students, part-time)
                                        salary_score = 0.9
                                    elif salary_val < 15_000:  # Very low - rare but possible
                                        salary_score = 0.3
                                        
                                    possible_splits.append((salary_val, capital_val, split_point, salary_score))
                    
                    if possible_splits:
                        # Pick the split with the best salary score
                        best_split = max(possible_splits, key=lambda x: x[3])  # x[3] is salary_score
                        salary, capital = best_split[0], best_split[1]
                    else:
                        # Fallback: use fixed rules
                        if len(parts) == 3:  # "40 500 577" -> salary "40 500", capital "577"
                            salary = self.swedish_number_to_int(' '.join(parts[:2]))
                            capital = self.swedish_number_to_int(parts[2])
                        elif len(parts) == 4:  # "630 000 275 896" -> split in middle  
                            salary = self.swedish_number_to_int(' '.join(parts[:2]))
                            capital = self.swedish_number_to_int(' '.join(parts[2:]))
                        elif len(parts) >= 5:  # Long amounts - assume first 3 parts are salary
                            salary = self.swedish_number_to_int(' '.join(parts[:3]))
                            capital = self.swedish_number_to_int(' '.join(parts[3:]))
                        else:
                            # Just take first part as salary, rest as capital
                            salary = self.swedish_number_to_int(parts[0])
                            capital = self.swedish_number_to_int(' '.join(parts[1:])) if len(parts) > 1 else 0
                    
            else:
                # Single number - use as salary
                salary = self.swedish_number_to_int(single_amount)
        
        # Sanity checks
        if salary > 50_000_000:
            salary = 0
        if abs(capital) > 10_000_000:
            capital = 0
            
        return salary, capital
    
    def is_valid_swedish_number_pattern(self, swedish_num_str):
        """Check if this forms a valid Swedish number pattern"""
        if not swedish_num_str.strip():
            return False
        
        parts = swedish_num_str.strip().split()
        
        # Single number is always valid
        if len(parts) == 1:
            return True
        
        # Swedish thousands are typically separated by spaces
        # Valid patterns: "20 800", "1 300", "5 474", "26 409"
        # Invalid patterns: "20 800 5" (odd number ending in single digit)
        
        # Check if all parts are numeric
        if not all(part.lstrip('-').isdigit() for part in parts):
            return False
        
        # For multi-part numbers, the last part should typically be 3 digits (like thousands)
        # unless it's a small number or has specific patterns
        if len(parts) >= 2:
            last_part = parts[-1].lstrip('-')
            first_parts = parts[:-1]
            
            # If last part is 1-2 digits and previous parts suggest this should be thousands format,
            # this is probably an invalid split
            if len(last_part) <= 2 and len(first_parts) >= 2:
                # This looks like "20 800 5" which should probably be "20 800" + "5"
                return False
        
        return True
    
    def swedish_number_to_int(self, swedish_num_str):
        """Convert Swedish number format to integer"""
        if not swedish_num_str or swedish_num_str.strip() == '0':
            return 0
        
        # Remove spaces to get the actual number
        clean_str = swedish_num_str.strip().replace(' ', '')
        
        try:
            return int(clean_str)
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
                
                # Show some samples with good salaries for verification
                good_salaries = [r for r in data if r['salary'] > 100000]
                if good_salaries:
                    print(f"  {len(good_salaries)} records with salary > 100k SEK")
                    sample = good_salaries[0]
                    print(f"  Sample: {sample['name']} - {sample['salary']:,} SEK")
                    
            except Exception as e:
                print(f"Error parsing {pdf_file.name}: {e}")
        
        return all_data

if __name__ == "__main__":
    parser = FinalWorkingParser()
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
            print(f"{row['name']:<30} {row['area_name']:<12} {row['salary']:8,} SEK")
        
        # Update database
        print("\nUpdating database with correctly parsed data...")
        from database import RatsitDatabase
        db = RatsitDatabase()
        db.insert_persons(data)
        print("Database updated with realistic salary data!")
        
        df.to_csv("final_working_parsed_data.csv", index=False)
        print("Data saved to final_working_parsed_data.csv")
        
    else:
        print("No data extracted")