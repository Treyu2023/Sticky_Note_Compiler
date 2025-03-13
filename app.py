from flask import Flask, render_template, request, jsonify
import os
import re
import json
from scripts.preferences import UserPreferences
from datetime import datetime

app = Flask(__name__)
DATA_DIR = os.path.join(os.getcwd(), "data")
user_prefs = UserPreferences()

def search_notes(query):
    results = []
    # Walk through each site directory under DATA_DIR
    for root, dirs, files in os.walk(DATA_DIR):
        for file in files:
            if file.endswith(".txt"):
                filepath = os.path.join(root, file)
                with open(filepath, "r", encoding="utf-8") as f:
                    content = f.read()
                # If query is empty or found in note, add to results
                if not query or re.search(re.escape(query), content, re.IGNORECASE):
                    # Get site name from directory structure
                    site = os.path.basename(root)
                    results.append({"site": site, "content": content})
    return results

def load_notes():
    """Load notes from the JSON file or database"""
    try:
        notes_path = os.path.join(DATA_DIR, 'notes.json')
        if os.path.exists(notes_path):
            with open(notes_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        else:
            # Check for individual site directories if notes.json doesn't exist
            notes = []
            for site_dir in os.listdir(DATA_DIR):
                site_path = os.path.join(DATA_DIR, site_dir)
                if os.path.isdir(site_path):
                    for file in os.listdir(site_path):
                        if file.endswith('.json'):
                            file_path = os.path.join(site_path, file)
                            with open(file_path, 'r', encoding='utf-8') as f:
                                equipment_notes = json.load(f)
                                equipment = file.replace('.json', '')
                                for note_data in equipment_notes:
                                    notes.append({
                                        "site": site_dir,
                                        "equipment": equipment,
                                        "content": note_data.get('content', ''),
                                        "date": note_data.get('date', datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
                                    })
            
            # Save the combined notes to notes.json for future use
            os.makedirs(DATA_DIR, exist_ok=True)
            with open(notes_path, 'w', encoding='utf-8') as f:
                json.dump(notes, f, indent=4)
            
            return notes
    except Exception as e:
        print(f"Error loading notes: {e}")
        # Create an empty notes file if it doesn't exist or has errors
        os.makedirs(DATA_DIR, exist_ok=True)
        with open(os.path.join(DATA_DIR, 'notes.json'), 'w', encoding='utf-8') as f:
            json.dump([], f)
        return []

def get_available_sites():
    """Get a list of all available sites from the notes data"""
    notes = load_notes()
    return sorted(list(set(note['site'] for note in notes if 'site' in note)))

@app.route('/', methods=['GET', 'POST'])
def index():
    search_query = request.form.get('search', '')
    site_filter = request.form.get('site_filter', '')
    date_filter = request.form.get('date_filter', '')
    error = None

    try:
        notes = load_notes()
        results = [note for note in notes if search_query.lower() in note.get('content', '').lower()]
        
        if site_filter:
            results = [note for note in results if note.get('site', '') == site_filter]
        
        # Apply date filter logic here if needed
        if date_filter:
            today = datetime.now().strftime('%Y-%m-%d')
            if date_filter == 'today':
                results = [note for note in results if note.get('date', '').startswith(today)]
            elif date_filter == 'week':
                # Simplified week filter - just check if date is within 7 days
                # A more robust implementation would use datetime calculations
                results = [note for note in results if 
                          note.get('date', '') >= (datetime.now().replace(day=datetime.now().day-7)).strftime('%Y-%m-%d')]
            elif date_filter == 'month':
                # Simplified month filter - just check if it's the current month and year
                current_month_year = datetime.now().strftime('%Y-%m')
                results = [note for note in results if 
                          note.get('date', '').startswith(current_month_year)]
        
        grouped_notes = {}
        for note in results:
            site = note.get('site', 'Unknown Site')
            if site not in grouped_notes:
                grouped_notes[site] = []
            grouped_notes[site].append(note)
        
        total_notes = len(results)
        unique_sites = len(grouped_notes)
        sites = get_available_sites()
        
        # Get user preferences for template
        theme = user_prefs.get_preference('theme', 'light')
        default_sort = user_prefs.get_preference('defaultSortOrder', 'date-desc')
        sidebar_expanded = user_prefs.get_preference('sidebarExpanded', True)
        
    except Exception as e:
        error = str(e)
        print(f"Error in index route: {e}")
        results = []
        grouped_notes = {}
        total_notes = 0
        unique_sites = 0
        sites = []
        theme = "light"
        default_sort = "date-desc"
        sidebar_expanded = True

    return render_template('index.html', 
                          notes=results, 
                          search_query=search_query, 
                          site_filter=site_filter, 
                          date_filter=date_filter, 
                          error=error, 
                          grouped_notes=grouped_notes, 
                          total_notes=total_notes, 
                          unique_sites=unique_sites,
                          sites=sites,
                          theme=theme,
                          default_sort=default_sort,
                          sidebar_expanded=sidebar_expanded)

@app.route('/api/notes', methods=['GET'])
def api_get_notes():
    query = request.args.get('search', '')
    site = request.args.get('site', '')
    
    try:
        notes = load_notes()
        results = [note for note in notes if query.lower() in note['content'].lower()]
        
        if site:
            results = [note for note in results if note['site'] == site]
            
        return jsonify({
            'success': True,
            'count': len(results),
            'notes': results
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        })

@app.route('/api/notes', methods=['POST'])
def api_add_note():
    try:
        note_data = request.json
        
        # Validate required fields
        if not note_data.get('content') or not note_data.get('site'):
            return jsonify({
                'success': False,
                'error': 'Content and site are required'
            }), 400
            
        # Add timestamp if not provided
        if 'date' not in note_data:
            from datetime import datetime
            note_data['date'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            
        # Load existing notes, add the new one, and save
        notes = load_notes()
        notes.append(note_data)
        
        with open('c:\\LocalStorage\\Sticky_Note_Compiler\\data\\notes.json', 'w') as f:
            json.dump(notes, f, indent=4)
            
        return jsonify({
            'success': True,
            'message': 'Note added successfully',
            'note': note_data
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/preferences', methods=['GET'])
def get_preferences():
    return jsonify(user_prefs.preferences)

@app.route('/api/preferences', methods=['POST'])
def update_preferences():
    try:
        new_prefs = request.json
        
        # Update all preferences
        for key, value in new_prefs.items():
            user_prefs.set_preference(key, value)
            
        return jsonify({
            'success': True,
            'message': 'Preferences updated successfully'
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/extract', methods=['POST'])
def api_extract_data():
    """Endpoint to trigger data extraction process"""
    try:
        from scripts.data_extractor import main as extract_main
        extract_main()
        return jsonify({
            'success': True,
            'message': 'Data extraction completed successfully'
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

if __name__ == "__main__":
    app.run(debug=True)
