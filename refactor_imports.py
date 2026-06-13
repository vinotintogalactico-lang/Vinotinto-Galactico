import os

replacements = {
    'from core.': 'from mundial.mundial_core.',
    'import core.': 'import mundial.mundial_core.',
    'from extractores.': 'from mundial.mundial_extractores.',
    'import extractores.': 'import mundial.mundial_extractores.',
    'core.excel_reader': 'mundial.mundial_core.excel_reader',
    'core.txt_exporter': 'mundial.mundial_core.txt_exporter',
    'core.html_exporter': 'mundial.mundial_core.html_exporter',
    'extractores.factory': 'mundial.mundial_extractores.factory',
}

def process_file(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    new_content = content
    for old, new in replacements.items():
        new_content = new_content.replace(old, new)
        
    if new_content != content:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(new_content)
        print(f"Updated {filepath}")

# Paths to process
paths_to_process = [
    r'E:\2-VG\VG_Extractor\pages\mundial.py',
]

for root, dirs, files in os.walk(r'E:\2-VG\VG_Extractor\mundial'):
    for file in files:
        if file.endswith('.py'):
            paths_to_process.append(os.path.join(root, file))

for p in paths_to_process:
    process_file(p)
