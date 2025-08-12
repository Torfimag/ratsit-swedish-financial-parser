# Ratsit Income Analytics App

A Flask web application that processes Swedish Ratsit salary data from PDF files and displays interactive visualizations with Stockholm area mapping and income rankings.

## Features

- 📄 **PDF Data Processing**: Extracts salary, capital income, and demographic data from Ratsit PDF files
- 🗺️ **Interactive Stockholm Map**: Shows income levels by postal code area with color-coded markers
- 📊 **Income Rankings**: Displays areas ranked by average salary
- 👑 **Top Earners**: Lists highest earning individuals across all areas
- 🏠 **Area Details**: Detailed breakdowns by postal code with all residents
- 📈 **Salary Distribution**: Chart showing income distribution across different ranges

## Installation

1. **Install dependencies**:
   ```bash
   pip3 install flask pdfplumber pandas folium
   ```

2. **Set up the database** (with sample data):
   ```bash
   python3 create_sample_data.py
   ```

3. **Run the web application**:
   ```bash
   python3 app.py
   ```

4. **Open your browser** to `http://localhost:5000`

## Data Processing

To process actual PDF files:

1. Place PDF files in the `pdfer/` directory
2. Run the processing script:
   ```bash
   python3 main.py
   ```

## File Structure

- `app.py` - Flask web application
- `database.py` - SQLite database operations
- `pdf_parser.py` - PDF data extraction (basic version)
- `improved_parser.py` - Enhanced PDF parsing
- `main.py` - Data processing pipeline
- `create_sample_data.py` - Generate sample data for testing
- `templates/` - HTML templates
- `pdfer/` - Directory containing PDF files

## Sample Data

The app comes with sample data from Bromma and Stockholm areas showing:
- High earners like Carlström Jonas (4M SEK) and Staaf Katarina (3.9M SEK)  
- Various income levels and demographics
- Different Stockholm postal codes

## Usage

1. **Dashboard**: Main page with map, rankings, and top earners
2. **Area Details**: Click on area names or map markers for detailed breakdowns
3. **Interactive Map**: Hover over markers to see income levels
4. **Color Coding**: Red (>1M SEK), Orange (750k-1M), Yellow (500k-750k), Green (<500k)

## Data Fields

- Name and address
- Age and income year  
- Postal code and area name
- Salary (employment income)
- Capital income
- Salary ranking within postal area
- Payment remarks (debt indicators)

## Technical Details

- **Backend**: Flask + SQLite
- **Frontend**: Bootstrap + Chart.js + Folium maps
- **PDF Processing**: pdfplumber library
- **Data Analysis**: pandas for statistics

The application handles Swedish characters and currency formatting, and includes defensive measures for data validation.