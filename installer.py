# Author: Elyes Rayane Melbouci
# Purpose: This script sets up a virtual environment, installs dependencies, creates a custom model file, and sets up a symlink for managing the script as a background service.

import os
import subprocess
import sys
from pathlib import Path
from tqdm import tqdm

def create_script(venv_path):
    script_dir = os.path.abspath(os.path.dirname(__file__))
    script_path = os.path.join(script_dir, 'remind_sansprint.py')
    
    script_content = f"""#!/bin/bash
if [ "$1" = "start" ]; then
    source {venv_path}/bin/activate
    python3 {script_path} &
    echo $! > /tmp/remind_sansprint.pid
elif [ "$1" = "close" ]; then
    if [ -f /tmp/remind_sansprint.pid ]]; then
        kill $(cat /tmp/remind_sansprint.pid)
        rm /tmp/remind_sansprint.pid
    else
        echo "No running instance found."
    fi
else
    echo "Usage: remindbg {{start|close}}"
fi
"""
    return script_content

def run_silent_command(command, progress_bar):
    """Run a command silently without printing output to the console."""
    subprocess.run(command, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    progress_bar.update(1)

def create_venv(venv_path, progress_bar):
    progress_bar.set_description("Creating virtual environment")
    run_silent_command([sys.executable, '-m', 'venv', venv_path], progress_bar)
    progress_bar.set_description("Upgrading pip")
    run_silent_command([os.path.join(venv_path, 'bin', 'pip'), 'install', '--upgrade', 'pip'], progress_bar)
    dependencies = ['easyocr', 'pillow', 'watchdog', 'pyaudio', 
                    'numpy', 'pyautogui', 'opencv-python', 'scikit-image', 
                    'flask', 'flask-socketio', 'flask-cors', 'langchain-community', 
                    'langchain-core', 'tiktoken', 'chromadb', 'rumps', 'psutil', 'ollama']
    for dependency in dependencies:
        progress_bar.set_description(f"Installing {dependency}")
        run_silent_command([os.path.join(venv_path, 'bin', 'pip'), 'install', dependency], progress_bar)

def create_custom_model_file(base_dir, progress_bar):
    progress_bar.set_description("Creating custom model file")
    model_content = """FROM LLAMA3

PARAMETER temperature 1

SYSTEM \"\"\"You are an artificial Memory assistant capable of retrieving and analyzing digital activity data.

Digital Activity Data:
* [Insert specific digital activity details here, such as search queries, website visits, or interactions.]

Response Format:
1. Answer: Provide a clear and concise answer to the question.
2. Details: Include specific details from the digital activity data to support your answer.
3. Do not tell the provided text but call it his digital activity.
4. If you do not know the answer based on the context, ask him questions to help find the answer.
5. If he asks you to summarize his activity, give him a bulletproof list of what he did.
\"\"\"
    """
    base_dir.mkdir(parents=True, exist_ok=True)
    with open(base_dir / "remind.ollama", "w") as file:
        file.write(model_content)
    progress_bar.update(1)

def create_and_pull_custom_model(base_dir, progress_bar):
    try:
        progress_bar.set_description("Creating custom model")
        run_silent_command(["ollama", "create", "-f", str(base_dir / "remind.ollama"), "Custom"], progress_bar)
        progress_bar.set_description("Pulling custom model")
        run_silent_command(["ollama", "pull", "Custom"], progress_bar)
    except subprocess.CalledProcessError as e:
        print(f"An error occurred while creating or pulling the custom model: {e}")
        if "pull" in str(e):
            print("It seems the model manifest does not exist. Please ensure the model was created successfully.")
    except FileNotFoundError:
        print("The ollama CLI is not installed or not found in the system path. Please install it and try again.")

def create_symlink(progress_bar):
    script_path = '/usr/local/bin/remindbg'
    venv_path = os.path.abspath(os.path.join(os.path.dirname(__file__), 'venv'))
    script_content = create_script(venv_path)

    try:
        progress_bar.set_description("Creating symlink")
        with open(script_path, 'w') as script_file:
            script_file.write(script_content)
        os.chmod(script_path, 0o755)
        print(f"Installation successful. Use 'remindbg start' to start and 'remindbg close' to stop the script.")
        progress_bar.update(1)
    except PermissionError:
        print("Permission denied. Please run this script with sudo.")
    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    base_dir = Path.home() / 'Library' / 'Application Support' / 'RemindEnchanted'
    venv_path = os.path.abspath(os.path.join(os.path.dirname(__file__), 'venv'))
    
    total_steps = 2 + 1 + 1 + 1 + 17  # Creating venv (2 steps), creating model file (1 step), creating and pulling model (2 steps), creating symlink (1 step), installing dependencies (17 steps)
    
    with tqdm(total=total_steps, desc="Starting installation") as progress_bar:
        create_venv(venv_path, progress_bar)
        create_custom_model_file(base_dir, progress_bar)
        create_and_pull_custom_model(base_dir, progress_bar)
        create_symlink(progress_bar)