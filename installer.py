import os
import subprocess
import sys
from pathlib import Path

def create_script(venv_path, script_path):
    script_content = f"""#!/bin/bash
if [ "$1" = "start" ]; then
    source {venv_path}/bin/activate
    python3 {script_path} &
    echo $! > ~/.remind_sansprint.pid
elif [ "$1" = "close" ]; then
    if [ -f ~/.remind_sansprint.pid ]; then
        kill $(cat ~/.remind_sansprint.pid)
        rm ~/.remind_sansprint.pid
    fi
else
    echo "Usage: remindbg {{start|close}}"
fi
"""
    return script_content

def run_silent_command(command):
    try:
        result = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True, text=True)
        return result.stdout
    except subprocess.CalledProcessError as e:
        print(f"Error: {e}")
        print(f"STDOUT: {e.stdout}")
        print(f"STDERR: {e.stderr}")
        raise

def create_venv(venv_path):
    system_python = "/usr/bin/python3"
    
    if not os.path.exists(system_python):
        raise FileNotFoundError(f"System Python not found at {system_python}")
    
    run_silent_command([system_python, '-m', 'venv', venv_path])
    
    venv_python = os.path.join(venv_path, 'bin', 'python')
    run_silent_command([venv_python, '-m', 'pip', 'install', '--upgrade', 'pip', 'setuptools', 'wheel'])
    
    dependencies_binary = ['pillow', 'numpy', 'rumps', 'scikit-image']
    dependencies_no_binary = ['watchdog', 'pyaudio', 'pyautogui', 'opencv-python',
                              'flask', 'flask-socketio', 'flask-cors', 'langchain-community', 
                              'langchain-core', 'tiktoken', 'chromadb', 'psutil', 'ollama']
    
    for dependency in dependencies_binary:
        run_silent_command([venv_python, '-m', 'pip', 'install', dependency])
    
    for dependency in dependencies_no_binary:
        run_silent_command([venv_python, '-m', 'pip', 'install', dependency])

def create_user_scripts(base_dir, venv_path):
    scripts_dir = base_dir / 'bin'
    scripts_dir.mkdir(parents=True, exist_ok=True)

    remindbg_path = scripts_dir / 'remindbg'
    script_path = Path(__file__).parent / 'remind_sansprint.py'
    script_content = create_script(venv_path, script_path)

    with open(remindbg_path, 'w') as script_file:
        script_file.write(script_content)
    remindbg_path.chmod(0o755)

    remindocr_source_path = Path(__file__).parent / 'RemindOCR'
    remindocr_dest_path = scripts_dir / 'RemindOCR'
    if not remindocr_dest_path.exists():
        remindocr_dest_path.symlink_to(remindocr_source_path)
    remindocr_dest_path.chmod(0o755)

    return scripts_dir

def update_user_path(scripts_dir):
    shell = os.environ.get("SHELL", "").split("/")[-1]
    if shell in ["bash", "zsh"]:
        rc_file = Path.home() / f".{shell}rc"
        with open(rc_file, "a") as f:
            f.write(f'\nexport PATH="$PATH:{scripts_dir}"\n')
        print(f"PATH updated in {rc_file}")
        print(f"Please restart your terminal or run 'source {rc_file}' to apply changes.")
    else:
        print(f"Please manually add {scripts_dir} to your PATH.")

if __name__ == "__main__":
    home = Path.home()
    base_dir = home / 'Library' / 'Application Support' / 'RemindEnchanted'
    base_dir.mkdir(parents=True, exist_ok=True)
    venv_path = base_dir / 'venv'
    
    create_venv(venv_path)
    scripts_dir = create_user_scripts(base_dir, venv_path)
    update_user_path(scripts_dir)
    print("Remind Service installed successfully.")