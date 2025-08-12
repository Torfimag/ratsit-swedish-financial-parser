import sqlite3
import pandas as pd
from pathlib import Path

class RatsitDatabase:
    def __init__(self, db_path="ratsit_data.db"):
        self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        """Initialize the database with required tables"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Create the main persons table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS persons (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                address TEXT,
                postal_code TEXT,
                area_name TEXT,
                age INTEGER,
                income_year INTEGER,
                salary_rank INTEGER,
                payment_remarks BOOLEAN,
                salary INTEGER,
                capital INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Create indexes for better performance
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_postal_code ON persons(postal_code)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_area_name ON persons(area_name)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_salary ON persons(salary)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_income_year ON persons(income_year)')
        
        # Create view for area statistics
        cursor.execute('''
            CREATE VIEW IF NOT EXISTS area_stats AS
            SELECT 
                postal_code,
                area_name,
                COUNT(*) as person_count,
                AVG(salary) as avg_salary,
                MIN(salary) as min_salary,
                MAX(salary) as max_salary,
                AVG(capital) as avg_capital,
                AVG(age) as avg_age
            FROM persons 
            WHERE salary > 0
            GROUP BY postal_code, area_name
        ''')
        
        conn.commit()
        conn.close()
    
    def insert_persons(self, persons_data):
        """Insert a list of person records into the database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Clear existing data
        cursor.execute('DELETE FROM persons')
        
        # Insert new data
        for person in persons_data:
            cursor.execute('''
                INSERT INTO persons 
                (name, address, postal_code, area_name, age, income_year, 
                 salary_rank, payment_remarks, salary, capital)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                person['name'],
                person['address'], 
                person['postal_code'],
                person['area_name'],
                person['age'],
                person['income_year'],
                person['salary_rank'],
                person['payment_remarks'],
                person['salary'],
                person['capital']
            ))
        
        conn.commit()
        conn.close()
        print(f"Inserted {len(persons_data)} records into database")
    
    def get_area_rankings(self):
        """Get areas ranked by average salary"""
        conn = sqlite3.connect(self.db_path)
        
        query = '''
            SELECT 
                postal_code,
                area_name,
                COUNT(*) as person_count,
                CAST(AVG(salary) AS INTEGER) as avg_salary,
                CAST(AVG(capital) AS INTEGER) as avg_capital,
                CAST(AVG(age) AS INTEGER) as avg_age
            FROM persons 
            GROUP BY postal_code, area_name
            ORDER BY avg_salary DESC, person_count DESC
        '''
        
        df = pd.read_sql_query(query, conn)
        conn.close()
        return df
    
    def get_persons_by_area(self, postal_code=None, area_name=None):
        """Get all persons for a specific area"""
        conn = sqlite3.connect(self.db_path)
        
        where_conditions = []
        params = []
        
        if postal_code:
            where_conditions.append("postal_code = ?")
            params.append(postal_code)
        
        if area_name:
            where_conditions.append("area_name = ?")
            params.append(area_name)
        
        where_clause = ""
        if where_conditions:
            where_clause = "WHERE " + " AND ".join(where_conditions)
        
        query = f'''
            SELECT * FROM persons 
            {where_clause}
            ORDER BY salary DESC
        '''
        
        df = pd.read_sql_query(query, conn, params=params)
        conn.close()
        return df
    
    def get_salary_distribution(self):
        """Get salary distribution data for visualization"""
        conn = sqlite3.connect(self.db_path)
        
        query = '''
            SELECT 
                area_name,
                postal_code,
                salary,
                salary_rank,
                age
            FROM persons 
            WHERE salary > 0
            ORDER BY salary DESC
        '''
        
        df = pd.read_sql_query(query, conn)
        conn.close()
        return df
    
    def get_top_earners(self, limit=50):
        """Get top earners across all areas"""
        conn = sqlite3.connect(self.db_path)
        
        query = '''
            SELECT 
                name,
                address, 
                area_name,
                postal_code,
                salary,
                capital,
                age,
                salary_rank
            FROM persons 
            ORDER BY salary DESC, salary_rank ASC
            LIMIT ?
        '''
        
        df = pd.read_sql_query(query, conn, params=(limit,))
        conn.close()
        return df

if __name__ == "__main__":
    # Test database functionality
    db = RatsitDatabase()
    print("Database initialized successfully")
    
    # Test with sample data
    sample_data = [
        {
            'name': 'Test Person',
            'address': 'Test Address',
            'postal_code': '167 72',
            'area_name': 'Bromma', 
            'age': 45,
            'income_year': 2023,
            'salary_rank': 100,
            'payment_remarks': False,
            'salary': 500000,
            'capital': 10000
        }
    ]
    
    db.insert_persons(sample_data)
    rankings = db.get_area_rankings()
    print("\nArea rankings:")
    print(rankings)