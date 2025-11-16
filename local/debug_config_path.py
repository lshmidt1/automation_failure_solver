import os
import sys

print("="*70)
print("DEBUG: Finding config.json")
print("="*70)

# Current working directory
cwd = os.getcwd()
print(f"\n1. Current Working Directory:")
print(f"   {cwd}")

# Check if config.json exists in CWD
config_in_cwd = os.path.join(cwd, "config.json")
print(f"\n2. Looking for config.json at:")
print(f"   {config_in_cwd}")
print(f"   Exists: {os.path.exists(config_in_cwd)}")

# Absolute path
abs_path = os.path.abspath("config.json")
print(f"\n3. Absolute path to config.json:")
print(f"   {abs_path}")
print(f"   Exists: {os.path.exists(abs_path)}")

# List all files in current directory
print(f"\n4. Files in current directory:")
files = [f for f in os.listdir(cwd) if os.path.isfile(os.path.join(cwd, f))]
for f in sorted(files)[:20]:
    if f.endswith('.json') or f.endswith('.py'):
        print(f"   {f}")

# Try to load config
print(f"\n5. Attempting to load config.json:")
try:
    import json
    with open('config.json', 'r') as f:
        config = json.load(f)
    print(f"   ✅ SUCCESS!")
    print(f"   local_repo_path: {config.get('local_repo_path', 'NOT FOUND')}")
except Exception as e:
    print(f"   ❌ FAILED: {e}")

print("="*70)
