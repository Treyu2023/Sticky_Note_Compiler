# Sticky Note Compiler

## Overview
This project extracts Windows Sticky Notes from `plum.sqlite`, cleans out any code or filler text—leaving only the user-entered content—and files each note into directories by site. The web portal lets you search these notes, displaying only the cleaned user data.

## Setup and Installation

1. **Create a Python Virtual Environment**  
   Open a terminal in this directory and run:
   ```
   python -m venv venv
   ```
   Activate the virtual environment:
   - On Windows:
     ```
     venv\Scripts\activate
     ```

2. **Install Dependencies**  
   With the virtual environment activated, run:
   ```
   pip install -r requirements.txt
   ```

## Running the Application

1. **Extract Sticky Notes**  
   Run the extraction script to process your sticky notes:
   ```
   python extract_notes.py
   ```
   This will create a `data` folder with subdirectories per site where each note is saved as a text file.

2. **Launch the Web Application**  
   Start the Flask server by running:
   ```
   python app.py
   ```
   Then open your browser and navigate to [http://127.0.0.1:5000](http://127.0.0.1:5000) to search through your notes.

## GitHub Repository Setup

Use the provided PowerShell script (`create_repo.ps1`) to create the local repository at `C:\LocalStorage\Sticky_Note_Compiler` and push it to your GitHub account (Treyu2023).  
Before using the script, ensure:
- Git and GitHub CLI (`gh`) are installed.
- You are authenticated with `gh auth login`.

## Additional Information

- The extraction script removes code-specific lines (e.g. those starting with `//`, `#`, or `/*`) so that only the user-entered data is preserved.
- Notes are categorized by site based on a “Site:” or “SiteID:” header in the note text.
- If no site header is found, the note is filed under **Uncategorized**.