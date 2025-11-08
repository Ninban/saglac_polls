import geopandas as gpd
import pandas as pd
import json
import sys
import os

def process_election_data(csv_filename, geojson_filename='polling_divisions.geojson', output_prefix=None):
    """
    Process election data from CSV and merge with GeoJSON polling division boundaries
    
    Parameters:
    csv_filename: Path to the election results CSV file
    geojson_filename: Path to the GeoJSON file with polling division boundaries
    output_prefix: Prefix for output files (defaults to CSV filename without extension)
    """
    
    # Set output prefix if not provided
    if output_prefix is None:
        output_prefix = os.path.splitext(os.path.basename(csv_filename))[0]
    
    # Read CSV data
    print(f"Reading CSV data from: {csv_filename}")
    csv_data = pd.read_csv(csv_filename)
    
    # Auto-detect column names
    column_mapping = detect_columns(csv_data)
    
    # Extract key column names
    district_num_col = column_mapping['district_number']
    district_name_col = column_mapping['district_name']
    pd_num_col = column_mapping['pd_number']
    pd_name_col = column_mapping['pd_name']
    candidate_cols = column_mapping['candidates']
    rejected_col = column_mapping['rejected']
    total_votes_col = column_mapping['total_votes']
    electors_col = column_mapping['electors']
    
    print(f"Detected columns:")
    print(f"  District Number: {district_num_col}")
    print(f"  District Name: {district_name_col}")
    print(f"  PD Number: {pd_num_col}")
    print(f"  PD Name: {pd_name_col}")
    print(f"  Candidates: {candidate_cols}")
    print(f"  Rejected: {rejected_col}")
    print(f"  Total Votes: {total_votes_col}")
    print(f"  Electors: {electors_col}")
    
    # Get district info from first row
    district_number = csv_data[district_num_col].iloc[0]
    district_name = csv_data[district_name_col].iloc[0]
    
    print(f"\nProcessing data for: {district_name} (District {district_number})")
    
    # Read GeoJSON
    print(f"Reading GeoJSON from: {geojson_filename}")
    gdf = gpd.read_file(geojson_filename)
    
    print(f"Total features in GeoJSON: {len(gdf)}")
    print(f"Unique FED_NUM values in GeoJSON: {gdf['FED_NUM'].unique()}")
    
    # Filter GeoJSON for target district
    gdf_district = gdf[gdf['FED_NUM'] == district_number]
    print(f"Features for District {district_number}: {len(gdf_district)}")
    
    # Clean and process CSV data
    csv_clean = filter_combined_rows(csv_data, candidate_cols[0])
    
    # Convert numeric columns
    numeric_cols = candidate_cols + [rejected_col, total_votes_col, electors_col]
    for col in numeric_cols:
        csv_clean[col] = pd.to_numeric(csv_clean[col], errors='coerce')
    
    # Convert PD number to integer
    csv_clean['PD_NUM'] = pd.to_numeric(csv_clean[pd_num_col].astype(str).str.strip(), errors='coerce').fillna(0).astype(int)
    
    # Get polling division names
    polling_division_names = csv_clean.groupby('PD_NUM')[pd_name_col].first().reset_index()
    polling_division_names.columns = ['PD_NUM', 'PD_NAME']
    
    # Aggregate by polling division number
    polling_division_results = csv_clean.groupby('PD_NUM')[numeric_cols].sum().reset_index()
    
    # Calculate percentages
    for candidate in candidate_cols:
        polling_division_results[f'{candidate}_pct'] = (
            polling_division_results[candidate] / polling_division_results[total_votes_col] * 100
        )
    
    # Find leading candidate for each polling division
    polling_division_results['leading_candidate'] = polling_division_results.apply(
        lambda row: find_leading_candidate(row, candidate_cols), axis=1
    )
    polling_division_results['leading_candidate_pct'] = polling_division_results.apply(
        lambda row: row[f"{row['leading_candidate']}_pct"], axis=1
    )
    
    # Merge with polling division names
    polling_division_results = polling_division_results.merge(polling_division_names, on='PD_NUM', how='left')
    
    print(f"Polling divisions in CSV: {polling_division_results['PD_NUM'].nunique()}")
    print(f"Polling divisions in filtered GeoJSON: {gdf_district['PD_NUM'].nunique()}")
    
    # Merge with GeoJSON
    merged_gdf = gdf_district.merge(
        polling_division_results, 
        on='PD_NUM', 
        how='inner'
    )
    
    print(f"Successfully merged features: {len(merged_gdf)}")
    
    # Convert to WGS84 for web mapping
    merged_gdf = merged_gdf.to_crs('EPSG:4326')
    
    # Save output files
    results_filename = f"{output_prefix}_election_results.geojson"
    simple_filename = f"{output_prefix}_election_simple.geojson"
    
    merged_gdf.to_file(results_filename, driver='GeoJSON')
    
    # Create simplified version
    simple_columns = ['PD_NUM', 'PD_NAME', 'geometry'] + numeric_cols + ['leading_candidate', 'leading_candidate_pct'] + [f'{candidate}_pct' for candidate in candidate_cols]
    simple_gdf = merged_gdf[simple_columns]
    simple_gdf.to_file(simple_filename, driver='GeoJSON')
    
    print(f"\nProcessing complete!")
    print(f"Created files:")
    print(f"- {results_filename} (full data)")
    print(f"- {simple_filename} (simplified for web)")
    
    # Show sample data
    print(f"\nSample of polling division names:")
    print(merged_gdf[['PD_NUM', 'PD_NAME']].head(10))
    
    return {
        'district_number': district_number,
        'district_name': district_name,
        'candidates': candidate_cols,
        'results_file': results_filename,
        'simple_file': simple_filename
    }

def detect_columns(df):
    """Auto-detect column names from the CSV structure"""
    columns = df.columns.tolist()
    
    # Common patterns for column names (English/French)
    patterns = {
        'district_number': ['Electoral District Number', 'Numéro de circonscription'],
        'district_name': ['Electoral District Name', 'Nom de circonscription'],
        'pd_number': ['Polling Division Number', 'Numéro de section de vote'],
        'pd_name': ['Polling Division Name', 'Nom de section de vote'],
        'rejected': ['Rejected Ballots', 'Bulletins rejetés'],
        'total_votes': ['Total Votes', 'Total des votes'],
        'electors': ['Electors', 'Électeurs']
    }
    
    detected = {}
    
    # Find standard columns
    for key, patterns in patterns.items():
        for pattern in patterns:
            matching_cols = [col for col in columns if pattern in col]
            if matching_cols:
                detected[key] = matching_cols[0]
                break
        else:
            print(f"Warning: Could not find column for {key}")
    
    # Find candidate columns (columns that are not the standard ones)
    standard_cols = list(detected.values())
    candidate_cols = [col for col in columns if col not in standard_cols and not any(x in col for x in ['rejected', 'total', 'elector', 'number', 'name', 'division'])]
    
    detected['candidates'] = candidate_cols
    
    return detected

def filter_combined_rows(df, first_candidate_col):
    """Filter out rows with combined results"""
    return df[~df[first_candidate_col].astype(str).str.contains('Combined', na=False)]

def find_leading_candidate(row, candidate_cols):
    """Find the candidate with the most votes in a row"""
    candidate_votes = {candidate: row[candidate] for candidate in candidate_cols}
    return max(candidate_votes, key=candidate_votes.get)

def main():
    """Main function to handle command line usage"""
    if len(sys.argv) < 2:
        print("Usage: python filtergeojson.py <csv_filename> [geojson_filename] [output_prefix]")
        print("Example: python filtergeojson.py pollbypoll_bureauparbureau24030.csv polling_divisions.geojson jonquiere")
        return
    
    csv_filename = sys.argv[1]
    geojson_filename = sys.argv[2] if len(sys.argv) > 2 else 'polling_divisions.geojson'
    output_prefix = sys.argv[3] if len(sys.argv) > 3 else None
    
    if not os.path.exists(csv_filename):
        print(f"Error: CSV file '{csv_filename}' not found")
        return
    
    if not os.path.exists(geojson_filename):
        print(f"Error: GeoJSON file '{geojson_filename}' not found")
        return
    
    try:
        result = process_election_data(csv_filename, geojson_filename, output_prefix)
        
        # Generate HTML template suggestion
        print(f"\n=== HTML TEMPLATE SUGGESTION ===")
        print(f"Use this configuration in your HTML file:")
        print(f"const candidateColors = {{")
        for candidate in result['candidates']:
            print(f'    "{candidate}": "#XXXXXX",')
        print(f"}};")
        print(f"// Load data from: {result['simple_file']}")
        
    except Exception as e:
        print(f"Error processing data: {e}")
        raise

if __name__ == "__main__":
    main()