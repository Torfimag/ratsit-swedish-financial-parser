#!/usr/bin/env python3

import sqlite3
from database import RatsitDatabase

# Check database contents
conn = sqlite3.connect('ratsit_data.db')
cursor = conn.cursor()

cursor.execute('SELECT COUNT(*) FROM persons')
total_count = cursor.fetchone()[0]
print(f'Total persons in database: {total_count}')

if total_count > 0:
    cursor.execute('SELECT * FROM persons LIMIT 10')
    print('\nSample records:')
    for row in cursor.fetchall():
        print(row)
    
    cursor.execute('SELECT postal_code, area_name, COUNT(*) as count FROM persons GROUP BY postal_code, area_name')
    print('\nBy area:')
    for row in cursor.fetchall():
        print(f'{row[1]} ({row[0]}): {row[2]} people')
else:
    print('Database is empty!')

conn.close()

# Test the RatsitDatabase class methods
db = RatsitDatabase()
rankings = db.get_area_rankings()
print(f'\nArea rankings query returned {len(rankings)} results')

top_earners = db.get_top_earners(10)
print(f'Top earners query returned {len(top_earners)} results')