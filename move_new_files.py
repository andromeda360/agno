import os
import shutil
import subprocess

def run_command(command):
    subprocess.check_call(command, shell=True)

def get_added_files():
    # Parse git status for "added by them" lines
    status_output = subprocess.check_output("git status --porcelain", shell=True).decode("utf-8")
    added_files = []
    for line in status_output.splitlines():
        # "added by them" usually shows up as "UA" or "A " depending on state
        # In a merge conflict where we deleted the dir, new files might be "UA" (unmerged, added by them)
        code = line[:2]
        filepath = line[3:]
        
        # We want files that are in libs/agno/ BUT NOT in libs/agno_v2/
        if filepath.startswith("libs/agno/") and "libs/agno_v2/" not in filepath:
             added_files.append(filepath)
    return added_files

def move_and_update(filepath):
    # Calculate new path
    new_path = filepath.replace("libs/agno/", "libs/agno_v2/")
    if "libs/agno/agno/" in filepath:
         new_path = filepath.replace("libs/agno/agno/", "libs/agno_v2/agno_v2/")
    
    # Ensure dest dir exists
    os.makedirs(os.path.dirname(new_path), exist_ok=True)
    
    # Git add the file first so we have it
    print(f"Adding {filepath}")
    run_command(f"git add {filepath}")
    
    # Move it
    if os.path.exists(filepath):
        print(f"Moving {filepath} -> {new_path}")
        if os.path.exists(new_path):
            print(f"Warning: {new_path} already exists, overwriting")
        shutil.move(filepath, new_path)
    else:
        print(f"Skipping move for {filepath} as it does not exist on disk")
        if not os.path.exists(new_path):
             print(f"Warning: neither source {filepath} nor dest {new_path} exist via move_new_files")
             return

    # Update imports in the new file
    with open(new_path, 'r') as f:
        content = f.read()
    
    # Simple replace - this covers most cases
    new_content = content.replace("from agno", "from agno_v2").replace("import agno", "import agno_v2")
    # Update env vars
    new_content = new_content.replace('"AGNO_', '"AGNO_V2_')
    
    with open(new_path, 'w') as f:
        f.write(new_content)
        
    # Stage the new file and the deletion of the old
    run_command(f"git add {new_path}")
    run_command(f"git rm --cached {filepath}")

files = get_added_files()
print(f"Found {len(files)} files to move")
for f in files:
    move_and_update(f)
