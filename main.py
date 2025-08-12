#!/usr/bin/env python3
"""
Main script to process PDFs and populate the database
"""

from final_working_parser import FinalWorkingParser
from database import RatsitDatabase
import sys

def main():
    print("Ratsit Data Processing")
    print("=" * 50)
    
    # Initialize components
    parser = FinalWorkingParser()
    db = RatsitDatabase()
    
    # Parse all PDFs
    print("Parsing PDF files...")
    pdf_data = parser.parse_all_pdfs("pdfer")
    
    if not pdf_data:
        print("No data extracted from PDFs. Exiting.")
        sys.exit(1)
    
    print(f"Successfully extracted {len(pdf_data)} records")
    
    # Insert data into database
    print("Inserting data into database...")
    db.insert_persons(pdf_data)
    
    # Show some statistics
    print("\nData processing completed!")
    print("\nArea Rankings by Average Salary:")
    rankings = db.get_area_rankings()
    print(rankings.to_string(index=False))
    
    print(f"\nTop 10 Highest Earners:")
    top_earners = db.get_top_earners(10)
    print(top_earners[['name', 'area_name', 'salary']].to_string(index=False))
    
    print(f"\nDatabase ready. You can now run 'python app.py' to start the web interface.")

if __name__ == "__main__":
    main()