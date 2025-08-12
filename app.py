#!/usr/bin/env python3
"""
Flask web application for visualizing Ratsit income data
"""

from flask import Flask, render_template, request, jsonify
from database import RatsitDatabase
import folium
import pandas as pd

app = Flask(__name__)

# Stockholm postal code coordinates (approximate centers)
STOCKHOLM_COORDINATES = {
    '167 72': (59.3293, 18.0686),  # Bromma
    '114 25': (59.3293, 18.0686),  # Södermalm (approximate)
    # Add more coordinates as needed
}

def create_stockholm_map(area_data):
    """Create a folium map of Stockholm with income data"""
    # Center on Stockholm
    m = folium.Map(
        location=[59.3293, 18.0686], 
        zoom_start=11,
        tiles='OpenStreetMap'
    )
    
    # Add markers for each area
    for _, row in area_data.iterrows():
        postal_code = row['postal_code']
        
        # Get coordinates (use default Stockholm center if not found)
        coords = STOCKHOLM_COORDINATES.get(postal_code, (59.3293, 18.0686))
        
        # Create popup text
        popup_text = f"""
        <b>{row['area_name']} ({postal_code})</b><br>
        Average Salary: {row['avg_salary']:,} SEK<br>
        Average Capital: {row['avg_capital']:,} SEK<br>
        Population: {row['person_count']} people<br>
        Average Age: {row['avg_age']} years
        """
        
        # Color code by salary level
        if row['avg_salary'] > 1000000:
            color = 'red'
        elif row['avg_salary'] > 750000:
            color = 'orange'  
        elif row['avg_salary'] > 500000:
            color = 'yellow'
        else:
            color = 'green'
        
        folium.Marker(
            coords,
            popup=folium.Popup(popup_text, max_width=300),
            tooltip=f"{row['area_name']}: {row['avg_salary']:,} SEK",
            icon=folium.Icon(color=color, icon='info-sign')
        ).add_to(m)
    
    return m

@app.route('/')
def index():
    """Main dashboard page"""
    db = RatsitDatabase()
    
    # Get sorting parameters for top earners
    sort_by = request.args.get('sort', 'salary')
    sort_order = request.args.get('order', 'desc')
    
    # Get area rankings
    area_rankings = db.get_area_rankings()
    
    # Get top earners with sorting
    top_earners = db.get_top_earners(20, sort_by=sort_by, sort_order=sort_order)
    
    # Create map
    stockholm_map = create_stockholm_map(area_rankings)
    map_html = stockholm_map._repr_html_()
    
    return render_template('index.html', 
                         area_rankings=area_rankings.to_dict('records'),
                         top_earners=top_earners.to_dict('records'),
                         map_html=map_html,
                         current_sort=sort_by,
                         current_order=sort_order)

@app.route('/area/<postal_code>')
def area_detail(postal_code):
    """Detail page for a specific area"""
    db = RatsitDatabase()
    
    # Get sorting parameters from query string
    sort_by = request.args.get('sort', 'salary')
    sort_order = request.args.get('order', 'desc')
    
    # Get persons in this area with sorting
    persons = db.get_persons_by_area(postal_code=postal_code, sort_by=sort_by, sort_order=sort_order)
    
    if persons.empty:
        return "Area not found", 404
    
    area_name = persons.iloc[0]['area_name']
    
    # Calculate statistics
    stats = {
        'area_name': area_name,
        'postal_code': postal_code,
        'total_people': len(persons),
        'avg_salary': int(persons['salary'].mean()),
        'max_salary': int(persons['salary'].max()),
        'min_salary': int(persons['salary'].min()),
        'avg_age': int(persons['age'].mean())
    }
    
    return render_template('area_detail.html',
                         stats=stats,
                         persons=persons.to_dict('records'),
                         current_sort=sort_by,
                         current_order=sort_order)

@app.route('/api/salary-distribution')
def salary_distribution():
    """API endpoint for salary distribution data"""
    db = RatsitDatabase()
    data = db.get_salary_distribution()
    
    # Group by salary ranges for visualization
    ranges = [
        (0, 300000, "Under 300k"),
        (300000, 500000, "300k-500k"),
        (500000, 750000, "500k-750k"), 
        (750000, 1000000, "750k-1M"),
        (1000000, float('inf'), "Over 1M")
    ]
    
    distribution = []
    for min_sal, max_sal, label in ranges:
        count = len(data[(data['salary'] >= min_sal) & (data['salary'] < max_sal)])
        distribution.append({'range': label, 'count': count})
    
    return jsonify(distribution)

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5002)