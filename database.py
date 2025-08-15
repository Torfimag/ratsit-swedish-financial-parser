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
    
    def get_persons_by_area(self, postal_code=None, area_name=None, sort_by='salary', sort_order='desc'):
        """Get all persons for a specific area with sorting"""
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
        
        # Validate sort parameters
        valid_columns = ['name', 'address', 'age', 'salary', 'capital', 'salary_rank']
        if sort_by not in valid_columns:
            sort_by = 'salary'
        
        if sort_order.lower() not in ['asc', 'desc']:
            sort_order = 'desc'
        
        # Map frontend column names to database column names
        column_mapping = {
            'rank': 'salary_rank'
        }
        db_column = column_mapping.get(sort_by, sort_by)
        
        query = f'''
            SELECT * FROM persons 
            {where_clause}
            ORDER BY {db_column} {sort_order.upper()}
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
    
    def get_top_earners(self, limit=50, sort_by='salary', sort_order='desc'):
        """Get top earners across all areas with sorting"""
        conn = sqlite3.connect(self.db_path)
        
        # Validate sort parameters
        valid_columns = ['name', 'address', 'age', 'salary', 'capital', 'salary_rank']
        if sort_by not in valid_columns:
            sort_by = 'salary'
        
        if sort_order.lower() not in ['asc', 'desc']:
            sort_order = 'desc'
        
        # Map frontend column names to database column names
        column_mapping = {
            'rank': 'salary_rank'
        }
        db_column = column_mapping.get(sort_by, sort_by)
        
        query = f'''
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
            ORDER BY {db_column} {sort_order.upper()}, salary_rank ASC
            LIMIT ?
        '''
        
        df = pd.read_sql_query(query, conn, params=(limit,))
        conn.close()
        return df
    
    def search_persons(self, search_term, limit=50):
        """Search for persons by name or address"""
        conn = sqlite3.connect(self.db_path)
        
        query = '''
            SELECT name, address, postal_code, area_name, age, salary, capital
            FROM persons 
            WHERE UPPER(name) LIKE UPPER(?) OR UPPER(address) LIKE UPPER(?)
            ORDER BY salary DESC
            LIMIT ?
        '''
        
        search_pattern = f'%{search_term}%'
        df = pd.read_sql_query(query, conn, params=(search_pattern, search_pattern, limit))
        conn.close()
        return df
    
    def get_top_capital_owners(self, limit=20):
        """Get top capital owners (highest capital income)"""
        conn = sqlite3.connect(self.db_path)
        
        query = '''
            SELECT name, area_name, capital, salary
            FROM persons 
            WHERE capital > 0
            ORDER BY capital DESC
            LIMIT ?
        '''
        
        df = pd.read_sql_query(query, conn, params=(limit,))
        conn.close()
        return df
    
    def get_loan_distribution_by_age(self):
        """Get loan distribution by age groups (negative capital = loans)"""
        conn = sqlite3.connect(self.db_path)
        
        query = '''
            SELECT 
                CASE 
                    WHEN age >= 20 AND age <= 29 THEN '20-29'
                    WHEN age >= 30 AND age <= 39 THEN '30-39'
                    WHEN age >= 40 AND age <= 49 THEN '40-49'
                    WHEN age >= 50 AND age <= 59 THEN '50-59'
                    WHEN age >= 60 AND age <= 69 THEN '60-69'
                    WHEN age >= 70 THEN '70+'
                    ELSE 'Under 20'
                END as age_group,
                COUNT(*) as total_people,
                SUM(CASE WHEN capital < 0 THEN 1 ELSE 0 END) as people_with_loans,
                COALESCE(ROUND(
                    100.0 * SUM(CASE WHEN capital < 0 THEN 1 ELSE 0 END) / COUNT(*), 1
                ), 0) as loan_percentage,
                COALESCE(AVG(CASE WHEN capital < 0 THEN ABS(capital) ELSE NULL END), 0) as avg_loan_amount
            FROM persons 
            WHERE age >= 20
            GROUP BY 
                CASE 
                    WHEN age >= 20 AND age <= 29 THEN '20-29'
                    WHEN age >= 30 AND age <= 39 THEN '30-39'
                    WHEN age >= 40 AND age <= 49 THEN '40-49'
                    WHEN age >= 50 AND age <= 59 THEN '50-59'
                    WHEN age >= 60 AND age <= 69 THEN '60-69'
                    WHEN age >= 70 THEN '70+'
                    ELSE 'Under 20'
                END
            ORDER BY age_group
        '''
        
        df = pd.read_sql_query(query, conn)
        conn.close()
        
        # Convert to list of dictionaries for JSON serialization
        result = []
        for _, row in df.iterrows():
            result.append({
                'age_group': row['age_group'],
                'total_people': int(row['total_people']),
                'people_with_loans': int(row['people_with_loans']),
                'loan_percentage': float(row['loan_percentage']) if pd.notna(row['loan_percentage']) else 0.0,
                'avg_loan_amount': float(row['avg_loan_amount']) if pd.notna(row['avg_loan_amount']) else 0.0
            })
        
        return result

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