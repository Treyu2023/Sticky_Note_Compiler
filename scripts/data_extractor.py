import os
import json
import re
import logging
import datetime
import sqlite3
from pathlib import Path
from typing import Dict, List, Any, Union, Optional, Tuple
import sys

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(os.path.join('c:', 'LocalStorage', 'Sticky_Note_Compiler', 'logs', 'data_extractor.log'), mode='a')
    ]
)
logger = logging.getLogger('data_extractor')

class DataExtractor:
    """
    Main class for extracting data from various sources like text files, 
    JSON, markdown notes, and other formats that might contain sticky notes.
    Specialized in extracting Windows Sticky Notes data.
    """
    
    def __init__(self, config_path: Optional[str] = None) -> None:
        """Initialize the data extractor with optional configuration."""
        self.project_dir = os.path.join('c:', 'LocalStorage', 'Sticky_Note_Compiler')
        
        # Create logs directory if it doesn't exist
        os.makedirs(os.path.join(self.project_dir, 'logs'), exist_ok=True)
        
        # Load configuration if provided
        self.config = {}
        if config_path:
            self.config = self._load_json(config_path)
        else:
            default_config_path = os.path.join(self.project_dir, 'config', 'extractor_config.json')
            if os.path.exists(default_config_path):
                self.config = self._load_json(default_config_path)
        
        # Windows Sticky Notes locations
        self.sticky_notes_paths = {
            'win10_plum': os.path.expanduser('~\\AppData\\Local\\Packages\\Microsoft.MicrosoftStickyNotes_8wekyb3d8bbwe\\LocalState\\plum.sqlite'),
            'win10_legacy': os.path.expanduser('~\\AppData\\Roaming\\Microsoft\\Sticky Notes\\StickyNotes.snt'),
            'win7': os.path.expanduser('~\\AppData\\Roaming\\Microsoft\\Sticky Notes')
        }
    
    def _load_json(self, file_path: str) -> Dict[str, Any]:
        """Load and parse JSON file with error handling."""
        try:
            if not os.path.exists(file_path):
                logger.warning(f"File not found: {file_path}")
                return {}
                
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read().strip()
                
            if not content:
                logger.warning(f"Empty file: {file_path}")
                return {}
                
            return json.loads(content)
        except json.JSONDecodeError as e:
            logger.error(f"JSON parsing error in {file_path}: {str(e)}")
            return {}
        except Exception as e:
            logger.error(f"Error loading file {file_path}: {str(e)}")
            return {}
    
    def _save_json(self, data: Dict[str, Any], file_path: str) -> bool:
        """Save data to JSON file with error handling."""
        try:
            directory = os.path.dirname(file_path)
            os.makedirs(directory, exist_ok=True)
            
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=4)
            return True
        except Exception as e:
            logger.error(f"Error saving to {file_path}: {str(e)}")
            return False
    
    def extract_from_file(self, file_path: str) -> Union[Dict[str, Any], List[Any], str, None]:
        """Extract data from a file based on its extension."""
        try:
            if not os.path.exists(file_path):
                logger.error(f"File not found: {file_path}")
                return None
                
            file_ext = os.path.splitext(file_path)[1].lower()
            
            if file_ext == '.json':
                return self._load_json(file_path)
                
            elif file_ext in ['.txt', '.md']:
                return self.extract_from_text_file(file_path)
                
            elif file_ext in ['.csv']:
                return self.extract_from_csv(file_path)
                
            else:
                logger.warning(f"Unsupported file type: {file_ext}")
                return None
                
        except Exception as e:
            logger.error(f"Error extracting from {file_path}: {str(e)}")
            return None
    
    def extract_from_text_file(self, file_path: str) -> Union[List[Dict[str, Any]], str]:
        """Extract notes or content from text/markdown files."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                
            # Try to identify notes in the content (using regex patterns)
            notes = self._identify_notes_in_text(content)
            if notes:
                return notes
            
            # If no structured notes were found, return raw content
            return content
        except Exception as e:
            logger.error(f"Error extracting from text file {file_path}: {str(e)}")
            return ""
    
    def extract_from_csv(self, file_path: str) -> List[Dict[str, Any]]:
        """Extract data from CSV files."""
        try:
            import csv
            results = []
            
            with open(file_path, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    results.append(dict(row))
            
            return results
        except Exception as e:
            logger.error(f"Error extracting from CSV file {file_path}: {str(e)}")
            return []
    
    def extract_from_win10_sticky_notes(self) -> List[Dict[str, Any]]:
        """Extract notes from Windows 10 Sticky Notes (plum.sqlite database)."""
        db_path = self.sticky_notes_paths['win10_plum']
        notes = []
        
        if not os.path.exists(db_path):
            logger.warning(f"Windows 10 Sticky Notes database not found at {db_path}")
            return notes
            
        try:
            # Connect to the SQLite database
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            # Try the modern schema first (Windows 10 newer versions)
            try:
                cursor.execute("SELECT Text, WindowPosition, Theme, Id, CreatedAt FROM Note")
                for row in cursor.fetchall():
                    text, position, theme, note_id, created_at = row
                    # Clean HTML tags from the text
                    clean_text = self._clean_html_content(text)
                    notes.append({
                        'title': clean_text.split('\n')[0] if clean_text else "Untitled Note",
                        'content': clean_text,
                        'position': position,
                        'theme': theme,
                        'id': note_id,
                        'created_at': created_at,
                        'source': 'windows_sticky_notes',
                        'extracted_at': datetime.datetime.now().isoformat()
                    })
            except sqlite3.OperationalError:
                # Try older schema
                logger.debug("Trying older Windows 10 Sticky Notes schema")
                cursor.execute("SELECT Text, WindowPosition, Theme FROM Notes")
                for i, row in enumerate(cursor.fetchall()):
                    text, position, theme = row
                    clean_text = self._clean_html_content(text)
                    notes.append({
                        'title': clean_text.split('\n')[0] if clean_text else f"Sticky Note {i+1}",
                        'content': clean_text,
                        'position': position,
                        'theme': theme,
                        'source': 'windows_sticky_notes',
                        'extracted_at': datetime.datetime.now().isoformat()
                    })
                    
            conn.close()
            logger.info(f"Extracted {len(notes)} notes from Windows 10 Sticky Notes")
            return notes
            
        except Exception as e:
            logger.error(f"Error extracting from Windows 10 Sticky Notes: {str(e)}")
            return []
    
    def _clean_html_content(self, html_content: str) -> str:
        """Clean HTML tags from sticky note content."""
        if not html_content:
            return ""
            
        # Remove RTF formatting if present
        if html_content.startswith('{\\rtf'):
            return self._extract_text_from_rtf(html_content)
            
        # Remove HTML tags
        clean_text = re.sub(r'<[^>]+>', '', html_content)
        
        # Handle special characters
        clean_text = clean_text.replace('&nbsp;', ' ')
        clean_text = clean_text.replace('&lt;', '<')
        clean_text = clean_text.replace('&gt;', '>')
        clean_text = clean_text.replace('&amp;', '&')
        
        # Remove multiple spaces and newlines
        clean_text = re.sub(r'\s+', ' ', clean_text)
        
        return clean_text.strip()
    
    def _extract_text_from_rtf(self, rtf_content: str) -> str:
        """Extract plain text from RTF content."""
        # Simple RTF parser - for complex RTF might need a dedicated library
        result = []
        in_control = False
        skip_next = False
        
        for char in rtf_content:
            if skip_next:
                skip_next = False
                continue
                
            if char == '\\':
                in_control = True
                continue
                
            if in_control:
                if char.isalpha():
                    continue
                else:
                    in_control = False
                    
            if not in_control and char != '{' and char != '}':
                result.append(char)
                
        return ''.join(result).strip()
    
    def extract_all_sticky_notes(self) -> List[Dict[str, Any]]:
        """Extract all available Sticky Notes from the system."""
        all_notes = []
        
        # Try Windows 10 modern Sticky Notes
        win10_notes = self.extract_from_win10_sticky_notes()
        if win10_notes:
            all_notes.extend(win10_notes)
            
        # Add legacy format extraction here if needed
            
        return all_notes
    
    def _identify_notes_in_text(self, content: str) -> List[Dict[str, Any]]:
        """
        Identify potential notes in text content with enhanced Sticky Notes recognition.
        Looks for patterns like markdown headers, bullet points, numbered lists, 
        or typical sticky note patterns.
        """
        notes = []
        
        # Look for markdown headers as potential note titles
        header_pattern = re.compile(r'^(#{1,6})\s+(.+)$', re.MULTILINE)
        headers = header_pattern.finditer(content)
        
        for match in headers:
            level = len(match.group(1))
            title = match.group(2).strip()
            
            # Find content until next header or end of text
            start_pos = match.end()
            next_header = header_pattern.search(content, start_pos)
            end_pos = next_header.start() if next_header else len(content)
            
            note_content = content[start_pos:end_pos].strip()
            
            notes.append({
                'title': title,
                'level': level,
                'content': note_content,
                'extracted_at': datetime.datetime.now().isoformat()
            })
        
        # If no headers found, try to identify by bullet points or numbered lists
        if not notes and ('\n- ' in content or re.search(r'\n\d+\. ', content)):
            bullet_pattern = re.compile(r'(?:^|\n)(?:- |\d+\. )(.+)(?:\n|$)')
            bullets = bullet_pattern.finditer(content)
            
            for i, match in enumerate(bullets):
                bullet_content = match.group(1).strip()
                notes.append({
                    'title': f"Note {i+1}",
                    'content': bullet_content,
                    'extracted_at': datetime.datetime.now().isoformat()
                })
        
        # Look for sticky note style text blocks (paragraphs separated by multiple newlines)
        if not notes:
            # Split by multiple newlines (common in copied sticky notes)
            sticky_blocks = re.split(r'\n{2,}', content)
            if len(sticky_blocks) > 1:
                for i, block in enumerate(sticky_blocks):
                    if block.strip():  # Skip empty blocks
                        title = block.split('\n')[0].strip() if block.strip() else f"Sticky Note {i+1}"
                        notes.append({
                            'title': title[:50] + ('...' if len(title) > 50 else ''),
                            'content': block.strip(),
                            'source': 'text_extraction',
                            'extracted_at': datetime.datetime.now().isoformat()
                        })
        
        return notes
    
    def extract_from_directory(self, directory_path: str, recursive: bool = True) -> Dict[str, Any]:
        """Extract data from all supported files in a directory."""
        results = {}
        
        try:
            if not os.path.exists(directory_path) or not os.path.isdir(directory_path):
                logger.error(f"Directory not found: {directory_path}")
                return results
                
            for item in os.listdir(directory_path):
                full_path = os.path.join(directory_path, item)
                
                if os.path.isfile(full_path):
                    ext = os.path.splitext(item)[1].lower()
                    if ext in ['.json', '.txt', '.md', '.csv']:
                        data = self.extract_from_file(full_path)
                        if data is not None:
                            results[item] = data
                
                elif os.path.isdir(full_path) and recursive:
                    sub_results = self.extract_from_directory(full_path, recursive)
                    if sub_results:
                        results[item] = sub_results
        
        except Exception as e:
            logger.error(f"Error extracting from directory {directory_path}: {str(e)}")
        
        return results
    
    def extract_from_clipboard(self) -> Union[str, Dict[str, Any], None]:
        """Extract data from system clipboard."""
        try:
            import pyperclip
            content = pyperclip.paste()
            
            if not content:
                logger.warning("Clipboard is empty")
                return None
                
            # Try to parse as JSON
            try:
                json_data = json.loads(content)
                return json_data
            except json.JSONDecodeError:
                pass
            
            # Check for note patterns in text
            notes = self._identify_notes_in_text(content)
            if notes:
                return notes
                
            # Return as raw text
            return content
            
        except ImportError:
            logger.error("pyperclip module not available for clipboard access")
            return None
        except Exception as e:
            logger.error(f"Error extracting from clipboard: {str(e)}")
            return None
    
    def save_extracted_data(self, data: Any, output_path: str) -> bool:
        """Save extracted data to the specified output path."""
        try:
            # Ensure directory exists
            directory = os.path.dirname(output_path)
            os.makedirs(directory, exist_ok=True)
            
            # Determine format based on file extension
            ext = os.path.splitext(output_path)[1].lower()
            
            if ext == '.json':
                return self._save_json(data, output_path)
            
            elif ext in ['.txt', '.md']:
                # Convert data to text format
                if isinstance(data, (dict, list)):
                    content = json.dumps(data, indent=2)
                else:
                    content = str(data)
                    
                with open(output_path, 'w', encoding='utf-8') as f:
                    f.write(content)
                return True
                
            else:
                logger.warning(f"Unsupported output format: {ext}")
                return False
                
        except Exception as e:
            logger.error(f"Error saving extracted data to {output_path}: {str(e)}")
            return False


# Command-line interface
if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Extract data from various sources, especially Windows Sticky Notes')
    parser.add_argument('--source', help='Source file or directory to extract from')
    parser.add_argument('--output', help='Output file path to save extracted data')
    parser.add_argument('--recursive', action='store_true', help='Recursively process directories')
    parser.add_argument('--config', help='Path to configuration file')
    parser.add_argument('--verbose', '-v', action='store_true', help='Enable verbose logging')
    parser.add_argument('--sticky-notes', action='store_true', help='Extract from Windows Sticky Notes')
    
    args = parser.parse_args()
    
    # Set logging level based on verbosity
    if args.verbose:
        logger.setLevel(logging.DEBUG)
    
    # Initialize extractor
    extractor = DataExtractor(args.config)
    
    # Process based on source type
    if args.sticky_notes:
        data = extractor.extract_all_sticky_notes()
    elif args.source and os.path.isfile(args.source):
        data = extractor.extract_from_file(args.source)
    elif args.source and os.path.isdir(args.source):
        data = extractor.extract_from_directory(args.source, args.recursive)
    elif args.source and args.source.lower() == 'clipboard':
        data = extractor.extract_from_clipboard()
    elif not args.source:
        # Default to sticky notes if no source specified
        data = extractor.extract_all_sticky_notes()
    else:
        logger.error(f"Invalid source: {args.source}")
        sys.exit(1)
    
    # Save or display results
    if data is not None:
        if args.output:
            success = extractor.save_extracted_data(data, args.output)
            if success:
                logger.info(f"Data successfully extracted and saved to {args.output}")
            else:
                logger.error(f"Failed to save data to {args.output}")
        else:
            # Print results to console
            if isinstance(data, (dict, list)):
                print(json.dumps(data, indent=2))
            else:
                print(data)
    else:
        logger.error("No data extracted")
        sys.exit(1)
