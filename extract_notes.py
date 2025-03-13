import os
import sqlite3
import re
from striprtf.striprtf import rtf_to_text

# ...existing code for obtaining plum.sqlite path...
username = os.getlogin()
plum_path = f'C:\\Users\\{username}\\AppData\\Local\\Packages\\Microsoft.MicrosoftStickyNotes_8wekyb3d8bbwe\\LocalState\\plum.sqlite'
if not os.path.exists(plum_path):
    print(f"Error: plum.sqlite not found at {plum_path}")
    exit(1)

# Connect and extract notes from the Sticky Notes DB
conn_plum = sqlite3.connect(plum_path)
cursor_plum = conn_plum.cursor()
cursor_plum.execute("SELECT Text FROM Note")
notes = cursor_plum.fetchall()
conn_plum.close()

# Ensure output folder exists
data_dir = os.path.join(os.getcwd(), "data")
os.makedirs(data_dir, exist_ok=True)

note_counter = {}

def clean_user_text(raw_text):
    # Remove RTF formatting
    plain_text = rtf_to_text(raw_text)
    # Remove extra whitespace and line breaks
    plain_text = re.sub(r'\n+', '\n', plain_text).strip()
    # Remove potential code blocks (lines starting with typical code markers)
    filtered_lines = []
    for line in plain_text.splitlines():
        # Discard lines that start with common code markers
        if re.match(r'^\s*(//|#|/\*|\*\s)', line):
            continue
        filtered_lines.append(line)
    return "\n".join(filtered_lines).strip()

for note in notes:
    user_text = clean_user_text(note[0])
    if not user_text:
        continue
    # Look for a "Site:" or "SiteID:" field in the note text
    site_match = re.search(r'(?:Site(?:ID)?):\s*([^\n]+)', user_text, re.IGNORECASE)
    site_folder = site_match.group(1).strip() if site_match else "Uncategorized"
    # Remove the site header from the note text so only user-entered data remains
    user_text = re.sub(r'(?:Site(?:ID)?):\s*[^\n]+\n?', '', user_text, flags=re.IGNORECASE).strip()
    # Create folder per site
    site_dir = os.path.join(data_dir, site_folder)
    os.makedirs(site_dir, exist_ok=True)
    # Generate unique filename for the note within the site folder
    note_counter.setdefault(site_folder, 0)
    note_counter[site_folder] += 1
    filename = f"note_{note_counter[site_folder]}.txt"
    filepath = os.path.join(site_dir, filename)
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(user_text)

print("Notes extracted, cleaned, and filed by site successfully.")
