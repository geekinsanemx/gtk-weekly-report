import json
import os
from pathlib import Path
from typing import Optional
from .models import AppState


class DataManager:
    def __init__(self, data_file: str = None):
        if data_file is None:
            # Use persistent location in user's home directory
            home_dir = Path.home()
            data_dir = home_dir / ".weekly-report-tracker"
            data_dir.mkdir(exist_ok=True)
            self.data_file = data_dir / "database.json"
        else:
            self.data_file = Path(__file__).parent.parent / data_file
            self.data_file.parent.mkdir(exist_ok=True)
        
        self.app_state: Optional[AppState] = None
        self._load_data()
    
    def _load_data(self) -> None:
        """Load data from JSON file or create new state"""
        try:
            if self.data_file.exists():
                with open(self.data_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                self.app_state = AppState.from_dict(data)
            else:
                self.app_state = AppState()
                self._save_data()
        except (json.JSONDecodeError, KeyError, ValueError) as e:
            print(f"Error loading data file: {e}")
            # Create backup of corrupted file
            if self.data_file.exists():
                backup_file = self.data_file.with_suffix('.json.backup')
                self.data_file.rename(backup_file)
                print(f"Corrupted file backed up as: {backup_file}")
            
            # Create new state
            self.app_state = AppState()
            self._save_data()
    
    def _save_data(self) -> None:
        """Save current state to JSON file"""
        try:
            # Create backup before saving
            if self.data_file.exists():
                backup_file = self.data_file.with_suffix('.json.tmp')
                with open(backup_file, 'w', encoding='utf-8') as f:
                    json.dump(self.app_state.to_dict(), f, indent=2, ensure_ascii=False)
                
                # Atomic replace
                backup_file.replace(self.data_file)
            else:
                with open(self.data_file, 'w', encoding='utf-8') as f:
                    json.dump(self.app_state.to_dict(), f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"Error saving data: {e}")
    
    def get_state(self) -> AppState:
        """Get current application state"""
        return self.app_state
    
    def add_work_entry(self, ticket: str, project: str, details: str = "") -> None:
        """Add new work entry and save"""
        self.app_state.add_work_entry(ticket, project, details)
        self._save_data()
    
    def update_current_work(self, ticket: Optional[str] = None, 
                          project: Optional[str] = None, 
                          details: Optional[str] = None) -> None:
        """Update current work state without creating new entry"""
        if ticket is not None:
            self.app_state.current_ticket = ticket
        if project is not None:
            self.app_state.current_project = project
        if details is not None:
            self.app_state.current_details = details
        
        self._save_data()
    
    def stop_current_work(self) -> None:
        """Stop current work session"""
        self.app_state.current_ticket = None
        self.app_state.current_project = None
        self.app_state.current_details = None
        self._save_data()
    
    def get_project_for_ticket(self, ticket: str) -> Optional[str]:
        """Get project name based on ticket using auto-detection"""
        return self.app_state.auto_detect_project(ticket)
    
    def get_current_week_summary(self) -> dict:
        """Get summary of current week's work"""
        entries = self.app_state.get_current_week_entries()
        
        projects_summary = {}
        total_time = 0
        
        for entry in entries:
            if entry.project not in projects_summary:
                projects_summary[entry.project] = {
                    'tickets': set(),
                    'time': 0,
                    'details': []
                }
            
            projects_summary[entry.project]['tickets'].add(entry.ticket)
            projects_summary[entry.project]['time'] += entry.duration
            if entry.details:
                projects_summary[entry.project]['details'].append(entry.details)
            
            total_time += entry.duration
        
        # Convert sets to lists for JSON serialization
        for project in projects_summary:
            projects_summary[project]['tickets'] = list(projects_summary[project]['tickets'])
        
        return {
            'total_time': total_time,
            'projects': projects_summary,
            'entries_count': len(entries)
        }
    
    def cleanup_test_data(self) -> int:
        """Remove test/demo data and return count of removed entries"""
        if not self.app_state:
            return 0
        
        original_count = len(self.app_state.work_entries)
        
        # Remove entries with test/demo patterns (expanded list)
        test_patterns = [
            'test', 'demo', 'example', 'sample', 'mock', 'fake', 'dummy',
            'added via status script', 'added via script', 'via script'
        ]
        self.app_state.work_entries = [
            entry for entry in self.app_state.work_entries
            if not any(pattern.lower() in entry.ticket.lower() or 
                      pattern.lower() in entry.project.lower() or
                      pattern.lower() in entry.details.lower()
                      for pattern in test_patterns)
        ]
        
        # Clear current work if it's test data
        if (self.app_state.current_ticket and 
            any(pattern.lower() in self.app_state.current_ticket.lower() or
                pattern.lower() in (self.app_state.current_project or "").lower()
                for pattern in test_patterns)):
            self.app_state.current_ticket = None
            self.app_state.current_project = None
            self.app_state.current_details = None
            self.app_state.last_activity = None
        
        # Remove test project mappings
        test_projects = []
        for project, mapping in self.app_state.project_mappings.items():
            if any(pattern.lower() in project.lower() for pattern in test_patterns):
                test_projects.append(project)
        
        for project in test_projects:
            del self.app_state.project_mappings[project]
        
        removed_count = original_count - len(self.app_state.work_entries)
        
        if removed_count > 0:
            self._save_data()
        
        return removed_count
    
    def get_data_location(self) -> str:
        """Get the location where data is stored"""
        return str(self.data_file)