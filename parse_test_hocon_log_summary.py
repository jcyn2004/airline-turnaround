import pandas as pd
import os
from collections import defaultdict

def extract_unique_values_from_csvs(directory_path):
    """
    Process all CSV files in a directory and extract unique values for each column.
    
    Parameters:
    directory_path (str): Path to the directory containing CSV files
    
    Returns:
    dict: Dictionary with column names as keys and lists of unique values as values
    """
    
    # Dictionary to store all values for each column
    column_values = defaultdict(list)
    
    # Get all CSV files in the directory
    csv_files = [f for f in os.listdir(directory_path) if f.endswith('.csv')]
    
    if not csv_files:
        print("No CSV files found in the directory.")
        return {}
    
    print(f"Found {len(csv_files)} CSV file(s) to process.")
    
    # Process each CSV file
    for csv_file in csv_files:
        file_path = os.path.join(directory_path, csv_file)
        print(f"Processing: {csv_file}")
        
        try:
            # Read the CSV file
            df = pd.read_csv(file_path)
            
            # Extract values from each column
            for column in df.columns:
                # Get non-null values from the column
                values = df[column].dropna().tolist()
                column_values[column].extend(values)
                
        except Exception as e:
            print(f"Error processing {csv_file}: {e}")
    
    # Remove duplicates from each column's values
    unique_column_values = {}
    for column, values in column_values.items():
        # Convert to set to remove duplicates, then back to list
        unique_values = list(set(values))
        unique_column_values[column] = sorted(unique_values)  # Optional: sort the values
        print(f"\nColumn '{column}': {len(unique_values)} unique values")
    
    return unique_column_values


# Example usage
if __name__ == "__main__":
    # Specify your directory path
    # directory_path = "."  # Current directory, change as needed
    directory_path = "/Users/971244/workspace/airline-turnaround/test_hocon/"
    
    # Extract unique values
    result = extract_unique_values_from_csvs(directory_path)
    
    # Display results
    print("\n" + "="*50)
    print("RESULTS")
    print("="*50)
    
    for column_name, unique_values in result.items():
        print(f"\n{column_name}:")
        print(f"  Count: {len(unique_values)}")
        print(f"  Values: {unique_values[:10]}")  # Show first 10 values
        if len(unique_values) > 10:
            print(f"  ... and {len(unique_values) - 10} more")