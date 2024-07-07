# Author: Elyes Rayane Melbouci
# Purpose: This script uninstalls the RemindEnchanted application by removing the virtual environment and the associated symlink.

import os
import shutil
from tqdm import tqdm
import subprocess

def run_silent_command(command, progress_bar):
    """Run a command silently without printing output to the console."""
    subprocess.run(command, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    progress_bar.update(1)

def remove_venv(venv_path, progress_bar):
    """Remove the virtual environment if it exists."""
    progress_bar.set_description("Removing virtual environment")
    if os.path.exists(venv_path):
        shutil.rmtree(venv_path)
        progress_bar.update(1)
        print(f"Virtual environment at {venv_path} has been removed.")
    else:
        progress_bar.update(1)
        print(f"No virtual environment found at {venv_path}.")

def remove_symlink(progress_bar):
    """Remove the symlink if it exists."""
    progress_bar.set_description("Removing symlink")
    script_path = '/usr/local/bin/remindbg'
    if os.path.exists(script_path):
        os.remove(script_path)
        progress_bar.update(1)
        print(f"Script {script_path} has been removed.")
    else:
        progress_bar.update(1)
        print(f"No script found at {script_path}.")

def main():
    venv_path = os.path.abspath(os.path.join(os.path.dirname(__file__), 'venv'))
    
    total_steps = 2  # Removing virtual environment (1 step), removing symlink (1 step)
    
    with tqdm(total=total_steps, desc="Starting uninstallation") as progress_bar:
        remove_venv(venv_path, progress_bar)
        remove_symlink(progress_bar)

if __name__ == "__main__":
    main()