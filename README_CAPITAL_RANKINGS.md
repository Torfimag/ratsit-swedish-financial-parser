# Capital Rankings Feature

## Overview
The Capital Rankings feature provides a comprehensive analysis of areas ranked by average capital income, offering insights into wealth distribution across Stockholm postal areas.

## Key Features

### 📊 **Area Capital Analysis**
- **18 analyzed areas** with statistical significance (minimum 5 residents)
- **Comprehensive metrics** including average capital, salary, population, and age
- **Capital vs. Debt analysis** showing both positive and negative capital areas

### 🏆 **Top Performing Areas by Capital**
1. **Bromma (167 71)**: 107,376 SEK average capital, 145 people
2. **Stockholm Södermalm (118 46)**: 71,546 SEK average capital, 280 people  
3. **Nacka (131 46)**: 47,833 SEK average capital, 383 people
4. **Saltsjö (132 48)**: 40,895 SEK average capital, 386 people
5. **Lidingö (181 29)**: 39,357 SEK average capital, 174 people

### 📉 **Areas with Debt Burden**
- **6 areas** with negative average capital (net debt)
- **Highest debt areas**:
  - Söderby (136 65): -22,755 SEK average capital
  - Hässelby (165 77): -8,588 SEK average capital
  - Skärholmen (127 45): -6,533 SEK average capital

### 📈 **Statistical Overview**
- **Capital Range**: -22,755 SEK to 107,376 SEK
- **Average Capital**: 21,174 SEK across all areas
- **Geographic Diversity**: From wealthy suburbs to student/immigrant areas

## Technical Implementation

### Database Features
- **Advanced SQL aggregation** with HAVING clauses for statistical relevance
- **Multi-metric analysis** combining capital, salary, age, and population data
- **Percentage calculations** for capital ownership rates

### Web Interface
- **Sortable columns** for all metrics (capital, salary, population, age)
- **Visual indicators** for top performers and debt areas
- **Responsive design** with Bootstrap styling
- **Integrated navigation** from main dashboard

### API Endpoints
- `/capital-rankings` - Main capital rankings page
- Linked to existing area detail pages for drill-down analysis

## Use Cases

### 💼 **Financial Analysis**
- Identify high-wealth areas for investment opportunities
- Understand debt distribution patterns
- Compare capital vs. salary relationships

### 🏘️ **Urban Planning**
- Area development prioritization
- Economic assistance targeting
- Infrastructure investment decisions

### 📊 **Research Applications**
- Socioeconomic studies
- Geographic wealth analysis
- Policy impact assessment

## Navigation
- **Main Dashboard** → Capital Rankings button in Area Rankings card
- **Navigation Bar** → Capital Rankings menu item
- **Area Details** → Click "View" button for individual area analysis

This feature provides valuable insights into the economic landscape of Stockholm, helping users understand wealth distribution patterns and make informed decisions based on comprehensive financial data.