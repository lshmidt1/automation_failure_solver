import re

print("=== Patching Backend for Training Integration ===\n")

# Read current backend
with open('app_testng_local_repo.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Check if already patched
if 'TRAINING_CONTENT' in content:
    print("✅ Backend already has training integration!")
    exit(0)

print("[1/3] Backing up current backend...")
import shutil
from datetime import datetime
timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
shutil.copy('app_testng_local_repo.py', f'app_testng_local_repo.py.backup_{timestamp}')
print(f"      ✅ Backup created: app_testng_local_repo.py.backup_{timestamp}")

print("\n[2/3] Adding training loader...")

# Find the line after LOCAL_REPO_PATH setup (around line 37)
# Add training loader after the config section
training_loader = '''
# Load agent training content
TRAINING_CONTENT = ""
try:
    training_path = os.path.join(os.path.dirname(__file__), 'AGENT_TRAINING.md')
    with open(training_path, 'r', encoding='utf-8') as f:
        TRAINING_CONTENT = f.read()
    print("✅ Loaded agent training file")
except Exception as e:
    print(f"⚠️ Could not load AGENT_TRAINING.md: {e}")
'''

# Insert after the LOCAL_REPO_PATH setup
lines = content.split('\n')
new_lines = []
inserted = False

for i, line in enumerate(lines):
    new_lines.append(line)
    # Insert after LOCAL_REPO_PATH = '' (around line 37)
    if "LOCAL_REPO_PATH = ''" in line and not inserted:
        new_lines.append(training_loader)
        inserted = True

content = '\n'.join(new_lines)
print("      ✅ Training loader added")

print("\n[3/3] Updating analyze function to use training...")

# Find the analyze function and add training to prompt
pattern = r'(def analyze_testng_failure_with_claude\(failure_data\):.*?prompt = f""")'
replacement = r'''\1
    
    # Add training section to prompt
    training_section = ""
    if TRAINING_CONTENT:
        training_section = TRAINING_CONTENT + "\n\n---\n\nNow apply the 6-step methodology above to this failure:\n\n"
    
    prompt = f"""{training_section}'''

content = re.sub(pattern, replacement, content, flags=re.DOTALL)

# Save updated backend
with open('app_testng_local_repo.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("      ✅ Analyze function updated")

print("\n" + "="*60)
print("✅ Backend successfully patched!")
print("="*60)
print("\nVerifying...")

# Verify
with open('app_testng_local_repo.py', 'r', encoding='utf-8') as f:
    new_content = f.read()
    
if 'TRAINING_CONTENT' in new_content and 'AGENT_TRAINING.md' in new_content:
    print("✅ Training integration verified")
    print("\nYou can now start the backend:")
    print('   $env:AWS_PROFILE="Claude-Code"; python app_testng_local_repo.py')
else:
    print("❌ Verification failed - check the file manually")
