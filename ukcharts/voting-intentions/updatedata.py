#!/usr/bin/env python3

import os
import shutil
import subprocess
import sys

def main():
    # Prompt user
    response = input("Do you want to update the data? (y/n): ").strip().lower()
    if response != 'y':
        print("Update cancelled.")
        return

    # Create backup folder
    backup_dir = 'backup'
    if not os.path.exists(backup_dir):
        os.makedirs(backup_dir)

    # Copy files to backup
    files_to_backup = ['ytod.csv', 'data.json']
    for file in files_to_backup:
        if os.path.exists(file):
            shutil.copy(file, os.path.join(backup_dir, file))
            print(f"Copied {file} to {backup_dir}/")
        else:
            print(f"Warning: {file} not found, skipping backup.")

    # Run loadwikitables.py
    print("\nRunning loadwikitables.py...")
    try:
        result = subprocess.run([sys.executable, 'loadwikitables.py'], capture_output=True, text=True)
        print("Output from loadwikitables.py:")
        print(result.stdout)
        if result.stderr:
            print("Errors:")
            print(result.stderr)
    except Exception as e:
        print(f"Error running loadwikitables.py: {e}")
        return

    # Ask if satisfied
    satisfied = input("Are you satisfied with the output? (y/n): ").strip().lower()
    if satisfied != 'y':
        print("Process stopped. You can restore from backup if needed.")
        return

    # Run process_data.py
    print("\nRunning process_data.py...")
    try:
        result = subprocess.run([sys.executable, 'process_data.py'], capture_output=True, text=True)
        print("Output from process_data.py:")
        print(result.stdout)
        if result.stderr:
            print("Errors:")
            print(result.stderr)
    except Exception as e:
        print(f"Error running process_data.py: {e}")

if __name__ == "__main__":
    main()