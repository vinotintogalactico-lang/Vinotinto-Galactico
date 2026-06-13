import os

paths_to_process = [
    r'E:\2-VG\VG_Extractor\pages\mundial.py',
]

for root, dirs, files in os.walk(r'E:\2-VG\VG_Extractor\mundial'):
    for file in files:
        if file.endswith('.py'):
            paths_to_process.append(os.path.join(root, file))

for filepath in paths_to_process:
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    new_content = content.replace('mundial.mundial_mundial.mundial_core.', 'mundial.mundial_core.')
    new_content = new_content.replace('mundial.mundial_mundial.mundial_extractores.', 'mundial.mundial_extractores.')
    new_content = new_content.replace('mundial.mundial_core', 'mundial.mundial_core') # just to be safe
    
    if new_content != content:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(new_content)
        print(f"Fixed {filepath}")
