import os
import json
import random
from datetime import datetime, timedelta

def generate_sample_data():
    """Generate sample data for testing the application."""
    sites = [
        "711 #36064 - King NC",
        "Great Stop 18 - Jamestown NC",
        "Fedex Ground 274 - Kernersville NC",
        "Site Alpha - Charlotte NC",
        "Main Street Location - Raleigh NC"
    ]
    
    equipment_types = [
        "FP 1", "FP 5", "FP 6", "FP 10", 
        "EN339811", "EN445932", 
        "GILM12893A001", "GILM45670B002",
        "T18699-G1", "T17622-G8"
    ]
    
    work_items = [
        "Replaced the PPU in the premium position. Tested successfully.",
        "Purged the CRIND to restore card reader functionality.",
        "Troubleshot and cleaned the door node PPUs and ribbon cable.",
        "Fixed E-stop circuit by replacing a blown fuse.",
        "Identified water intrusion in the electrical housing.",
        "Re-activated the card reader and tested all functions.",
        "Replaced faulty backlights for premium and plus displays.",
        "Installed new monochrome display on left side keypad.",
        "Fixed communication issues between D-Box and CRINDs.",
        "Replaced damaged ribbon cable and reconnected components."
    ]
    
    # Generate random dates within the last 30 days
    def random_date():
        days_ago = random.randint(0, 30)
        date = datetime.now() - timedelta(days=days_ago)
        return date.strftime('%Y-%m-%d %H:%M:%S')
    
    # Generate 20 sample notes
    notes = []
    for _ in range(20):
        site = random.choice(sites)
        equipment = random.choice(equipment_types)
        
        # Create a detailed note with multiple work items
        work_count = random.randint(1, 3)
        selected_work = random.sample(work_items, work_count)
        content = f"Work performed on {equipment}:\n\n"
        content += "\n".join(f"• {item}" for item in selected_work)
        
        notes.append({
            "site": site,
            "equipment": equipment,
            "content": content,
            "date": random_date()
        })
    
    return notes

def save_sample_data():
    """Save the generated sample data to the notes.json file."""
    data_dir = 'c:\\LocalStorage\\Sticky_Note_Compiler\\data'
    os.makedirs(data_dir, exist_ok=True)
    
    notes = generate_sample_data()
    notes_file = os.path.join(data_dir, 'notes.json')
    
    with open(notes_file, 'w', encoding='utf-8') as f:
        json.dump(notes, f, indent=4)
    
    print(f"Saved {len(notes)} sample notes to {notes_file}")
    
    # Also create site/equipment structure
    structured_data = {}
    for note in notes:
        site = note["site"]
        equipment = note["equipment"]
        
        if site not in structured_data:
            structured_data[site] = {}
        
        if equipment not in structured_data[site]:
            structured_data[site][equipment] = []
        
        structured_data[site][equipment].append({
            "content": note["content"],
            "date": note["date"]
        })
    
    # Save the structured data
    for site, equipment_data in structured_data.items():
        site_dir = os.path.join(data_dir, site.replace("/", "_").replace("\\", "_"))
        os.makedirs(site_dir, exist_ok=True)
        
        for equipment, notes_data in equipment_data.items():
            equipment_file = os.path.join(site_dir, f"{equipment.replace('/', '_').replace('\\', '_')}.json")
            with open(equipment_file, 'w', encoding='utf-8') as f:
                json.dump(notes_data, f, indent=4)

if __name__ == "__main__":
    print("Generating sample data...")
    save_sample_data()
    print("Sample data generation completed!")
