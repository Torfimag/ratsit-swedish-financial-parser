# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a Python Flask application that processes Swedish Ratsit salary data from PDF files and displays it in an interactive web interface with Stockholm area mapping and income rankings.

## Architecture

The application consists of several key components:

- **pdf_parser.py**: Extracts structured data from Ratsit PDF files using pdfplumber, parsing names, addresses, postal codes, salaries, capital income, and other demographic data
- **database.py**: SQLite database layer with schema for persons table and area statistics views
- **app.py**: Flask web application providing dashboard, area detail pages, and JSON APIs
- **main.py**: Data processing pipeline that coordinates PDF parsing and database insertion
- **templates/**: Jinja2 templates with Bootstrap UI for responsive web interface

## Common Development Commands

### Data Processing
```bash
# Process all PDFs and populate database
python main.py

# Test individual components
python pdf_parser.py
python database.py
```

### Web Application
```bash
# Run Flask development server
python app.py

# Access application at http://localhost:5000
```

### Dependencies
```bash
# Install required packages
pip install -r requirements.txt
```

## Data Structure

The application processes PDF data with these key fields:
- Name, address, postal code, area name
- Age, income year, salary ranking within postal area
- Salary (employment income) and capital income
- Payment remarks (debt markers)

## Key Features

- **PDF Processing**: Robust parsing of Swedish text with special characters
- **Geographic Mapping**: Folium integration with Stockholm postal code coordinates
- **Income Analytics**: Area rankings, salary distributions, top earners
- **Responsive UI**: Bootstrap-based interface with interactive maps and charts

## Database Schema

The main `persons` table stores individual records with indexes on postal_code, area_name, salary, and income_year. An `area_stats` view provides aggregated statistics for geographic analysis.

## Swedish Language Support

The codebase handles Swedish characters (åäöÅÄÖ) and Ratsit-specific data formats including postal codes (format "XXX XX") and Swedish kronor amounts.