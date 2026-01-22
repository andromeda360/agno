import os
import re
import subprocess

def get_conflict_files():
    # Use grep to find files with conflict markers
    try:
        output = subprocess.check_output(['grep', '-r', '-l', '<<<<<<<', 'libs/agno_v2'], text=True)
        return output.splitlines()
    except subprocess.CalledProcessError:
        return []

def resolve_file(filepath):
    print(f"Resolving {filepath}")
    with open(filepath, 'r') as f:
        content = f.read()
    
    # Regex to match conflict blocks and capture HEAD content
    # Handles potential varying whitespace or newline at end
    # Note: re.DOTALL makes . match newlines
    pattern = re.compile(r'<<<<<<< HEAD.*?\n(.*?)\n=======\n.*?\n>>>>>>> .*?\n', re.DOTALL)
    
    new_content = pattern.sub(r'\1\n', content) # Add newline to be safe, or capture it?
    
    # Better capture:
    # Capture everything between <<<< HEAD... and =======
    # content is group 1
    
    def replacer(match):
        return match.group(1)

    new_content = pattern.sub(replacer, content)
    
    # Check if markers remain (nested or failed match)
    if '<<<<<<<' in new_content:
        print(f"Warning: markers remain in {filepath}")
        
    with open(filepath, 'w') as f:
        f.write(new_content)

files = get_conflict_files()
print(f"Found {len(files)} files to resolve")
for f in files:
    resolve_file(f)
