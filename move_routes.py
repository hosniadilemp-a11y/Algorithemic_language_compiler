# Python script to move the routes
import sys

with open('/media/hp/Data/Lab-ISI/HOSNI/AlgoCompiler/src/web/app.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

new_lines = []
routes_lines = []
in_routes = False

for i, line in enumerate(lines):
    if line.startswith('if __name__ == "__main__":') or line.startswith("if __name__ == '__main__':"):
        split_idx = i
        break

split_idx1 = split_idx
split_idx2 = split_idx

# the routes we appended earlier started with @app.route('/api/problems'
for i, line in enumerate(lines):
    if line.startswith('@app.route(\'/api/problems\','):
        split_idx2 = i
        break

if split_idx2 > split_idx1:
   main_block = lines[split_idx1:split_idx2]
   routes_block = lines[split_idx2:]
   new_lines = lines[:split_idx1] + routes_block + main_block
   
   with open('/media/hp/Data/Lab-ISI/HOSNI/AlgoCompiler/src/web/app.py', 'w', encoding='utf-8') as f:
       f.writelines(new_lines)
   print("Moved routes successfully")
else:
   print("Routes not found at the bottom")
