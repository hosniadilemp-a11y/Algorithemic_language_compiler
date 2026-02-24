import os
import re

def update_file(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Case insensitive replacement for "Fin Si" -> "Finsi"
    new_content = re.sub(r'(?i)\bFin\s+Si\b', 'Finsi', content)
    # Case insensitive replacement for "Fin Pour" -> "Finpour"
    new_content = re.sub(r'(?i)\bFin\s+Pour\b', 'Finpour', new_content)
    
    if new_content != content:
        print(f"Updating {filepath}")
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(new_content)

def main():
    dirs = [
        r"c:\Users\adel\Documents\Python Codes\AlgoCompiler\examples",
        r"c:\Users\adel\Documents\Python Codes\AlgoCompiler\tests"
    ]
    for d in dirs:
        if os.path.exists(d):
            for filename in os.listdir(d):
                if filename.endswith(".algo") or filename.endswith(".py"):
                    update_file(os.path.join(d, filename))

if __name__ == "__main__":
    main()
