# Author: Elyes Rayane Melbouci
# Purpose: This script resets the data by deleting the specified directory and all its contents.

import os
import shutil
from pathlib import Path
from tqdm import tqdm

def reset_data(progress_bar):
    """Reset the data by deleting the specified directory and all its contents."""
    progress_bar.set_description("Resetting data")
    # Path to the directory to be deleted
    data_dir = Path.home() / 'Library' / 'Application Support' / 'RemindEnchanted'
    
    # Check if the directory exists
    if data_dir.exists() and data_dir.is_dir():
        # Delete the directory and all its contents
        shutil.rmtree(data_dir)
        progress_bar.update(1)
        print(f"All data in {data_dir} has been reset.")
    else:
        progress_bar.update(1)
        print(f"No data found at {data_dir}.")

if __name__ == "__main__":
    total_steps = 1  # Resetting data (1 step)
    
    with tqdm(total=total_steps, desc="Starting reset") as progress_bar:
        reset_data(progress_bar)