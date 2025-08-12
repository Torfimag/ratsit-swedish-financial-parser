#!/usr/bin/env python3
"""Create sample data based on the PDF content we can see"""

from database import RatsitDatabase

def create_sample_data():
    """Create sample data based on the Bromma PDF we analyzed"""
    
    # Sample data from the PDF content visible in the document
    sample_data = [
        {
            'name': 'Kindström Magnus',
            'address': 'Djupdalsvägen 114',
            'postal_code': '167 72',
            'area_name': 'Bromma',
            'age': 53,
            'income_year': 2023,
            'salary_rank': 80,
            'payment_remarks': False,
            'salary': 932500,
            'capital': -129720
        },
        {
            'name': 'Alexandre Thomas',
            'address': 'Gökvägen 2',
            'postal_code': '167 72',
            'area_name': 'Bromma',
            'age': 54,
            'income_year': 2023,
            'salary_rank': 170,
            'payment_remarks': False,
            'salary': 630000,
            'capital': 275896
        },
        {
            'name': 'Antonsson Bill Mikael',
            'address': 'Stugvägen 8',
            'postal_code': '167 72',
            'area_name': 'Bromma',
            'age': 38,
            'income_year': 2023,
            'salary_rank': 4,
            'payment_remarks': False,
            'salary': 3385000,
            'capital': -20156
        },
        {
            'name': 'Carlström Jonas',
            'address': 'Stugvägen 3',
            'postal_code': '167 72',
            'area_name': 'Bromma',
            'age': 46,
            'income_year': 2023,
            'salary_rank': 1,
            'payment_remarks': False,
            'salary': 4000900,
            'capital': -88780
        },
        {
            'name': 'Staaf Katarina',
            'address': 'Stugvägen 1',
            'postal_code': '167 72',
            'area_name': 'Bromma',
            'age': 57,
            'income_year': 2023,
            'salary_rank': 2,
            'payment_remarks': False,
            'salary': 3945000,
            'capital': 45365
        },
        {
            'name': 'Allvin Catharina',
            'address': 'Stugvägen 42',
            'postal_code': '167 72',
            'area_name': 'Bromma',
            'age': 53,
            'income_year': 2022,
            'salary_rank': 254,
            'payment_remarks': False,
            'salary': 435055,
            'capital': -25172
        },
        {
            'name': 'Andersson Sverker',
            'address': 'Stugvägen 25',
            'postal_code': '167 72',
            'area_name': 'Bromma',
            'age': 59,
            'income_year': 2023,
            'salary_rank': 53,
            'payment_remarks': False,
            'salary': 1055700,
            'capital': -82556
        },
        # Add some data from other areas
        {
            'name': 'Eriksson Anna',
            'address': 'Storgatan 15',
            'postal_code': '111 29',
            'area_name': 'Stockholm City',
            'age': 42,
            'income_year': 2023,
            'salary_rank': 125,
            'payment_remarks': False,
            'salary': 750000,
            'capital': 15000
        },
        {
            'name': 'Johansson Per',
            'address': 'Vasagatan 8',
            'postal_code': '111 20',
            'area_name': 'Stockholm City',
            'age': 38,
            'income_year': 2023,
            'salary_rank': 89,
            'payment_remarks': False,
            'salary': 890000,
            'capital': 45000
        },
        {
            'name': 'Nilsson Eva',
            'address': 'Hornsgatan 45',
            'postal_code': '118 20',
            'area_name': 'Södermalm',
            'age': 35,
            'income_year': 2023,
            'salary_rank': 67,
            'payment_remarks': False,
            'salary': 680000,
            'capital': 12000
        }
    ]
    
    return sample_data

if __name__ == "__main__":
    print("Creating sample database with realistic data...")
    
    # Initialize database
    db = RatsitDatabase()
    
    # Create and insert sample data
    sample_data = create_sample_data()
    db.insert_persons(sample_data)
    
    print(f"Inserted {len(sample_data)} sample records")
    
    # Show some statistics
    rankings = db.get_area_rankings()
    print("\nArea Rankings:")
    print(rankings)
    
    print("\nTop Earners:")
    top_earners = db.get_top_earners(5)
    print(top_earners[['name', 'area_name', 'salary']])
    
    print("\nSample data created! You can now run 'python3 app.py' to see the web interface.")