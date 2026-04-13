import io
path = r'c:\Users\linksweld\Documents\zelda-multi-launcher-hub\python_src\launcher_core.py'
with io.open(path, 'r', encoding='utf-8') as f:
    lines = f.readlines()

for i, line in enumerate(lines):
    if 'def load_save_state(self, slot: int): pass' in line:
        print "Line", i+1, ":", repr(line)
