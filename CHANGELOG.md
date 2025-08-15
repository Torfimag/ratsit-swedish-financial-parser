# Changelog

All notable changes to this project will be documented in this file.

## [Unreleased]

### Added
- Column-aware postal code parsing to fix multi-column PDF issues
- Comprehensive postal code break handling in PDF parser
- Debug logging for postal code detection and column assignment

### Fixed
- **Critical parsing bug**: Postal code breaks in multi-column PDFs no longer cause missing records
- Records below postal code breaks now correctly parsed with appropriate postal codes
- Missing persons (Oksa Ana Liza Namata, Skottefors Tommy, Özdeveci Osman) now successfully extracted

### Changed
- Updated main parsing pipeline to use `FixedPostalParser` instead of `FinalWorkingParser`
- Improved column detection algorithm for better spatial awareness in PDF parsing

## [1.4.0] - 2025-01-15

### Added
- Search functionality for names and streets with Swedish character support
- Top 20 capital owners list on dashboard
- Loan percentage distribution by age groups (20-29, 30-39, etc.)
- Interactive Chart.js visualization for loan distribution
- Comprehensive error handling for JSON data parsing

### Enhanced
- Dashboard layout reorganized into 3-column structure
- Added COALESCE and proper data type casting in SQL queries
- Improved search with case-insensitive matching and URL encoding

### Fixed
- Empty loan distribution chart due to NaN values in JSON
- Search functionality case sensitivity issues with Swedish characters
- Data type casting errors in age group aggregations

## [1.3.0] - 2025-01-15

### Added
- Column sorting functionality for data tables
- Sortable headers with Font Awesome icons for name, address, age, salary, capital, and rank
- Toggle logic for ascending/descending sort orders
- URL parameter handling for sort state persistence

### Enhanced
- Database queries with sorting parameters
- Area detail pages with interactive column headers
- Visual indicators for current sort column and direction

## [1.2.0] - 2025-01-15

### Added
- Re-parsing capability for all PDF files in directory
- Updated record count from 1,850 to 4,559 across 16 PDF files
- Comprehensive PDF processing with `FinalWorkingParser`

### Enhanced
- Data freshness with latest PDF content
- Improved parsing accuracy and coverage

## [1.1.0] - 2025-01-15

### Added
- Initial CLAUDE.md documentation with project overview
- Development workflow documentation
- Architecture descriptions and command references
- Swedish language support documentation

### Enhanced
- Codebase analysis and comprehensive documentation
- Development guidelines and best practices

## [1.0.0] - 2025-01-15

### Added
- Initial release of Swedish financial data parsing application
- Flask web application with interactive dashboard
- SQLite database with persons table and area statistics views
- PDF parsing using pdfplumber for Ratsit salary data
- Geographic mapping with Folium and Stockholm postal codes
- Bootstrap-based responsive UI
- Income analytics with area rankings and salary distributions

### Core Features
- PDF processing of Swedish text with special characters
- Multi-column PDF layout parsing
- Swedish kronor amount parsing
- Interactive maps and charts
- Area-based income analysis

---

## Development Log

### 2025-01-16 00:35 UTC - Dashboard UI Features Restored
- **Added**: Search functionality for names and street addresses with case-insensitive matching
- **Added**: Top 20 capital owners list with highest capital income
- **Added**: Loan percentage distribution by age groups (20-29, 30-39, etc.) with interactive charts
- **Enhanced**: Dashboard layout reorganized into 3-column structure for better UX
- **API Endpoints**: `/search`, `/api/loan-distribution` for dynamic data
- **Files Modified**: database.py, app.py, templates/index.html, created templates/search_results.html
- **Features Working**: ✅ Search, ✅ Capital owners list, ✅ Age-based loan distribution chart
- **Status**: All requested UI features fully restored and functional

### 2025-01-16 00:25 UTC - System Restored to Stable State
- **Action**: Restored project to last working Git commit due to parser issues
- **Files Restored**: main.py, app.py, database.py, templates/index.html
- **Broken Parsers Removed**: definitive_parser.py, fixed_postal_parser.py, column_aware_parser.py, spatial_aware_parser.py, hybrid_spatial_parser.py, ultimate_parser.py
- **Current Status**: Back to stable FinalWorkingParser with 5,245 records successfully processing
- **Result**: System fully operational with proven working parser

### 2025-01-15 23:55 UTC - Reverted to Previous Parser
- **Issue**: Fixed postal parser caused performance/accuracy issues
- **Action**: Reverted main.py to use FinalWorkingParser instead of FixedPostalParser
- **Reason**: User reported the new parser "did not work and is now bad"
- **Files Modified**: `main.py` 
- **Status**: Back to stable parsing state

### 2025-01-15 23:45 UTC - Postal Code Break Fix Completed
- **Issue**: Multi-column PDF parsing failed when postal codes appeared mid-page
- **Root Cause**: Postal codes were applied globally instead of column-specifically
- **Solution**: Created `fixed_postal_parser.py` with column-aware postal code handling
- **Impact**: Recovered missing records, improved parsing accuracy
- **Files Modified**: 
  - Created `fixed_postal_parser.py`
  - Updated `main.py` to use new parser
- **Records**: Database now contains 4,808 records (up from previous count)
- **Validation**: Successfully found previously missing persons:
  - Oksa Ana Liza Namata: 224 26 N - 53,700 SEK
  - Skottefors Tommy: 162 64 Vällingby - 0 SEK  
  - Özdeveci Osman: 424 98 N - 317,600 SEK

### 2025-01-15 22:30 UTC - Dashboard Enhancements Deployed
- **Added**: Search functionality with Swedish character support
- **Added**: Top 20 capital owners list 
- **Added**: Loan distribution chart by age groups
- **Fixed**: NaN value handling in JSON responses
- **Files Modified**: `database.py`, `app.py`, `templates/index.html`
- **Testing**: All new features validated and working

### 2025-01-15 21:15 UTC - Column Sorting Implementation
- **Added**: Interactive column sorting for all data tables
- **Enhanced**: Area detail pages with sortable headers
- **Files Modified**: `database.py`, `app.py`, `templates/area_detail.html`
- **UI**: Font Awesome icons for sort indicators

### 2025-01-15 20:00 UTC - Project Documentation Created
- **Created**: Comprehensive CLAUDE.md with project overview
- **Documented**: Architecture, development commands, and key features
- **Added**: Swedish language support notes and database schema

### 2025-01-15 19:00 UTC - Initial System Analysis
- **Analyzed**: Existing Flask application codebase
- **Reviewed**: PDF parsing, database layer, and web interface
- **Identified**: Core functionality and improvement opportunities