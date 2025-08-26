from dataclasses import dataclass, field
from datetime import datetime, date
from typing import Dict, List, Optional
import json


@dataclass
class WorkEntry:
    timestamp: datetime
    ticket: str
    project: str
    details: str = ""
    duration: int = 60  # minutes, default 1 hour
    
    def to_dict(self) -> Dict:
        return {
            "timestamp": self.timestamp.isoformat(),
            "ticket": self.ticket,
            "project": self.project,
            "details": self.details,
            "duration": self.duration
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'WorkEntry':
        return cls(
            timestamp=datetime.fromisoformat(data["timestamp"]),
            ticket=data["ticket"],
            project=data["project"],
            details=data.get("details", ""),
            duration=data.get("duration", 60)
        )


@dataclass
class ProjectMapping:
    ticket_patterns: List[str] = field(default_factory=list)
    name: str = ""
    
    def to_dict(self) -> Dict:
        return {
            "ticket_patterns": self.ticket_patterns,
            "name": self.name
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'ProjectMapping':
        return cls(
            ticket_patterns=data.get("ticket_patterns", []),
            name=data.get("name", "")
        )


@dataclass
class AppState:
    current_ticket: Optional[str] = None
    current_project: Optional[str] = None
    current_details: Optional[str] = None
    last_activity: Optional[datetime] = None
    work_entries: List[WorkEntry] = field(default_factory=list)
    project_mappings: Dict[str, ProjectMapping] = field(default_factory=dict)
    
    def to_dict(self) -> Dict:
        return {
            "current_ticket": self.current_ticket,
            "current_project": self.current_project,
            "current_details": self.current_details,
            "last_activity": self.last_activity.isoformat() if self.last_activity else None,
            "work_entries": [entry.to_dict() for entry in self.work_entries],
            "project_mappings": {k: v.to_dict() for k, v in self.project_mappings.items()}
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'AppState':
        return cls(
            current_ticket=data.get("current_ticket"),
            current_project=data.get("current_project"),
            current_details=data.get("current_details"),
            last_activity=datetime.fromisoformat(data["last_activity"]) if data.get("last_activity") else None,
            work_entries=[WorkEntry.from_dict(entry) for entry in data.get("work_entries", [])],
            project_mappings={k: ProjectMapping.from_dict(v) for k, v in data.get("project_mappings", {}).items()}
        )
    
    def get_current_week_entries(self) -> List[WorkEntry]:
        """Get all work entries for current week (Monday to Sunday)"""
        today = date.today()
        week_start = today - timedelta(days=today.weekday())
        week_end = week_start + timedelta(days=6)
        
        return [
            entry for entry in self.work_entries
            if week_start <= entry.timestamp.date() <= week_end
        ]
    
    def get_week_entries_with_offset(self, week_offset: int) -> List[WorkEntry]:
        """Get work entries for a specific week offset from current week
        
        Args:
            week_offset: Weeks offset from current week (0=current, -1=last week, etc.)
        """
        today = date.today()
        current_week_start = today - timedelta(days=today.weekday())
        target_week_start = current_week_start + timedelta(weeks=week_offset)
        target_week_end = target_week_start + timedelta(days=6)
        
        return [
            entry for entry in self.work_entries
            if target_week_start <= entry.timestamp.date() <= target_week_end
        ]
    
    def auto_detect_project(self, ticket: str) -> Optional[str]:
        """Auto-detect project based on ticket patterns"""
        for project, mapping in self.project_mappings.items():
            for pattern in mapping.ticket_patterns:
                if pattern.lower() in ticket.lower():
                    return project
        return None
    
    def add_work_entry(self, ticket: str, project: str, details: str = "") -> None:
        """Add a new work entry and update current state"""
        entry = WorkEntry(
            timestamp=datetime.now(),
            ticket=ticket,
            project=project,
            details=details
        )
        self.work_entries.append(entry)
        
        self.current_ticket = ticket
        self.current_project = project
        self.current_details = details
        self.last_activity = entry.timestamp
        
        # Update project mappings for future auto-detection
        if project not in self.project_mappings:
            self.project_mappings[project] = ProjectMapping(name=project)
        
        ticket_prefix = ticket.split('-')[0] if '-' in ticket else ticket[:3]
        if ticket_prefix not in self.project_mappings[project].ticket_patterns:
            self.project_mappings[project].ticket_patterns.append(ticket_prefix)


from datetime import timedelta