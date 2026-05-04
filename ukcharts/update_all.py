import subprocess
import os
import sys

def run_command(command, cwd):
    print(f'>>> Updating {cwd}...')
    try:
        # Using subprocess.run with default stdin/stdout to allow interactivity
        subprocess.run(command, cwd=cwd, check=True)
    except subprocess.CalledProcessError as e:
        print(f'Error updating {cwd}: {e}')
    except Exception as e:
        print(f'Unexpected error: {e}')

def main():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    
    # 1. Update Leaders (Automated)
    leaders_dir = os.path.join(base_dir, 'leaders')
    if os.path.exists(leaders_dir):
        run_command(['uv', 'run', 'get_leaders_table.py'], cwd=leaders_dir)
    
    # 2. Update Voting Intentions (Interactive)
    voting_dir = os.path.join(base_dir, 'voting-intentions')
    if os.path.exists(voting_dir):
        run_command(['uv', 'run', 'updatedata.py'], cwd=voting_dir)

    print('All updates completed.')

if __name__ == '__main__':
    main()
