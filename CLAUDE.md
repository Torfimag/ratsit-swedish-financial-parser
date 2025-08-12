# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a Python Flask application that processes Swedish Ratsit salary data from PDF files and displays it in an interactive web interface with Stockholm area mapping and income rankings.

## Architecture

The application consists of several key components:

- **pdf_parser.py**: Core PDF extraction using pdfplumber with regex patterns for structured data parsing
- **database.py**: SQLite database layer with `persons` table and `area_stats` view for aggregated analytics
- **app.py**: Flask web application with routes for dashboard, area details, and JSON APIs
- **main.py**: Data processing pipeline that orchestrates PDF parsing and database population
- **templates/**: Jinja2 templates with Bootstrap UI, interactive maps (Folium), and Chart.js visualizations

Multiple parser variants exist (improved_parser.py, final_parser.py, etc.) representing development iterations - pdf_parser.py is the current stable version.

## Common Development Commands

### Dependencies and Setup
```bash
# Install required packages
pip install -r requirements.txt

# Create sample data for testing (without PDF files)
python create_sample_data.py
```

### Data Processing
```bash
# Process all PDFs in pdfer/ directory and populate database
python main.py

# Test database operations independently
python database.py

# Check database contents and structure
python check_db.py
```

### Web Application
```bash
# Run Flask development server
python app.py

# Access application at http://localhost:5000
```

### Development and Testing
```bash
# Debug PDF parsing with specific files
python debug_parser.py

# Test amount parsing specifically
python debug_amounts.py
```

## Data Processing Pipeline

1. **PDF Input**: Place Ratsit PDF files in `pdfer/` directory
2. **Parsing**: `main.py` calls `RatsitPDFParser.parse_all_pdfs()` to extract structured data
3. **Database**: Parsed data inserted via `RatsitDatabase.insert_persons()`
4. **Validation**: Parser handles Swedish characters, currency formatting, and data validation
5. **Analytics**: `area_stats` view provides real-time aggregations for the web interface

## Database Schema

### persons table
- Core fields: name, address, postal_code, area_name, age, income_year
- Financial: salary, capital, salary_rank, payment_remarks
- Indexes on postal_code, area_name, salary, income_year for performance

### area_stats view
- Aggregated statistics: person_count, avg_salary, min/max_salary, avg_capital, avg_age
- Grouped by postal_code and area_name for geographic analysis

## Key Features and Components

- **Swedish Text Processing**: Handles åäöÅÄÖ characters and Swedish postal code format (XXX XX)
- **Geographic Mapping**: Folium integration with Stockholm coordinates, color-coded salary markers
- **PDF Data Extraction**: Regex-based parsing of Ratsit-specific PDF layouts and formatting
- **Interactive Analytics**: Area rankings, top earners, salary distributions with Chart.js
- **Responsive Design**: Bootstrap-based templates with mobile-friendly navigation

## Development Notes

- Multiple parser files exist as development iterations - use pdf_parser.py as the primary implementation
- Stockholm coordinates are hardcoded in app.py for postal code mapping
- Sample data generation available via create_sample_data.py for development without PDFs
- Application handles Swedish kronor formatting and negative capital values
- Database operations use pandas DataFrames for efficient bulk operations