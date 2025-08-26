from datetime import datetime, date, timedelta
from pathlib import Path
from typing import List, Dict
from .models import WorkEntry, AppState


class ReportGenerator:
    def __init__(self, output_dir: str = None):
        if output_dir is None:
            # Use persistent location in user's home directory
            home_dir = Path.home()
            self.output_dir = home_dir / ".weekly-report-tracker" / "reports"
        else:
            self.output_dir = Path(__file__).parent.parent / output_dir
        
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    def generate_weekly_report(self, app_state: AppState, week_offset: int = 0) -> str:
        """Generate weekly report and return file path
        
        Args:
            app_state: Application state containing work entries
            week_offset: Weeks offset from current week (0=current, -1=last week, etc.)
        """
        if week_offset == 0:
            entries = app_state.get_current_week_entries()
        else:
            entries = app_state.get_week_entries_with_offset(week_offset)
        
        # Calculate week dates based on offset
        today = date.today()
        current_week_start = today - timedelta(days=today.weekday())
        target_week_start = current_week_start + timedelta(weeks=week_offset)
        target_week_end = target_week_start + timedelta(days=6)
        
        if not entries:
            return self._generate_empty_report(target_week_start, target_week_end)
        
        report_content = self._create_report_content(entries, target_week_start, target_week_end)
        
        # Create filename with week dates
        filename = f"weekly_report_{target_week_start.strftime('%Y%m%d')}-{target_week_end.strftime('%Y%m%d')}.md"
        report_path = self.output_dir / filename
        
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write(report_content)
        
        return str(report_path)
    
    def _generate_empty_report(self, week_start: date = None, week_end: date = None) -> str:
        """Generate report when no work entries exist"""
        if week_start is None or week_end is None:
            today = date.today()
            week_start = today - timedelta(days=today.weekday())
            week_end = week_start + timedelta(days=6)
        
        content = f"""# Weekly Report
**Week:** {week_start.strftime('%m/%d/%Y')} - {week_end.strftime('%m/%d/%Y')}

---

## Summary
No activities were recorded this week.

---
"""
        
        filename = f"weekly_report_{week_start.strftime('%Y%m%d')}-{week_end.strftime('%Y%m%d')}.md"
        report_path = self.output_dir / filename
        
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        return str(report_path)
    
    def _create_report_content(self, entries: List[WorkEntry], week_start: date = None, week_end: date = None) -> str:
        """Create formatted report content"""
        if week_start is None or week_end is None:
            today = date.today()
            week_start = today - timedelta(days=today.weekday())
            week_end = week_start + timedelta(days=6)
        
        # Group entries by project
        projects_data = self._group_entries_by_project(entries)
        
        # Calculate totals
        total_hours = sum(entry.duration for entry in entries) / 60
        total_entries = len(entries)
        
        content = f"""# Weekly Report
**Week:** {week_start.strftime('%m/%d/%Y')} - {week_end.strftime('%m/%d/%Y')}

---

## Executive Summary
- **Total hours worked:** {total_hours:.1f} hours
- **Total entries:** {total_entries}
- **Projects worked on:** {len(projects_data)}

---

"""
        
        # Add projects section
        for project_name, project_data in projects_data.items():
            content += self._create_project_section(project_name, project_data)
        
        # Add daily breakdown
        content += self._create_daily_breakdown(entries)
        
        content += "\n---\n"
        
        return content
    
    def _group_entries_by_project(self, entries: List[WorkEntry]) -> Dict:
        """Group entries by project"""
        projects = {}
        
        for entry in entries:
            if entry.project not in projects:
                projects[entry.project] = {
                    'tickets': set(),
                    'total_time': 0,
                    'entries': [],
                    'details': []
                }
            
            projects[entry.project]['tickets'].add(entry.ticket)
            projects[entry.project]['total_time'] += entry.duration
            projects[entry.project]['entries'].append(entry)
            
            if entry.details and entry.details not in projects[entry.project]['details']:
                projects[entry.project]['details'].append(entry.details)
        
        return projects
    
    def _create_project_section(self, project_name: str, project_data: Dict) -> str:
        """Create formatted project section grouped by tickets"""
        hours = project_data['total_time'] / 60
        
        section = f"""## {project_name}
**Total time:** {hours:.1f} hours

"""
        
        # Group entries by ticket for this project
        ticket_groups = {}
        for entry in project_data['entries']:
            if entry.ticket not in ticket_groups:
                ticket_groups[entry.ticket] = {
                    'entries': [],
                    'total_time': 0,
                    'details': set()
                }
            ticket_groups[entry.ticket]['entries'].append(entry)
            ticket_groups[entry.ticket]['total_time'] += entry.duration
            if entry.details:
                ticket_groups[entry.ticket]['details'].add(entry.details)
        
        # Add each ticket section
        for ticket, ticket_data in sorted(ticket_groups.items()):
            ticket_hours = ticket_data['total_time'] / 60
            section += f"### {ticket}\n"
            section += f"**Time spent:** {ticket_hours:.1f} hours  \n"
            section += f"**Sessions:** {len(ticket_data['entries'])}\n\n"
            
            if ticket_data['details']:
                section += "**Activities:**\n"
                for detail in sorted(ticket_data['details']):
                    section += f"- {detail}\n"
                section += "\n"
        
        return section
    
    def _create_daily_breakdown(self, entries: List[WorkEntry]) -> str:
        """Create daily breakdown section"""
        # Group entries by day
        daily_entries = {}
        days_en = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
        
        for entry in entries:
            day_key = entry.timestamp.date()
            if day_key not in daily_entries:
                daily_entries[day_key] = []
            daily_entries[day_key].append(entry)
        
        section = "## Daily Breakdown\n\n"
        
        # Sort days
        for day in sorted(daily_entries.keys()):
            day_name = days_en[day.weekday()]
            day_entries = daily_entries[day]
            day_hours = sum(entry.duration for entry in day_entries) / 60
            
            section += f"### {day_name} {day.strftime('%m/%d')}\n"
            section += f"**Total:** {day_hours:.1f} hours\n\n"
            
            # Group by project for the day
            day_projects = {}
            for entry in day_entries:
                if entry.project not in day_projects:
                    day_projects[entry.project] = []
                day_projects[entry.project].append(entry)
            
            for project, project_entries in day_projects.items():
                project_hours = sum(entry.duration for entry in project_entries) / 60
                tickets = set(entry.ticket for entry in project_entries)
                
                section += f"- **{project}** ({project_hours:.1f}h): {', '.join(tickets)}\n"
            
            section += "\n"
        
        return section
    
    def get_report_path(self, date_str: str = None) -> Path:
        """Get path for report file"""
        if date_str:
            filename = f"weekly_report_{date_str}.md"
        else:
            today = date.today()
            week_start = today - timedelta(days=today.weekday())
            week_end = week_start + timedelta(days=6)
            filename = f"weekly_report_{week_start.strftime('%Y%m%d')}-{week_end.strftime('%Y%m%d')}.md"
        
        return self.output_dir / filename
    
    def list_available_reports(self) -> List[str]:
        """List all available report files"""
        if not self.output_dir.exists():
            return []
        
        reports = []
        for file_path in self.output_dir.glob("weekly_report_*.md"):
            reports.append(str(file_path))
        
        return sorted(reports, reverse=True)  # Most recent first
    
    def get_available_weeks(self) -> List[dict]:
        """Get list of available weeks with date ranges"""
        if not self.output_dir.exists():
            return []
        
        weeks = []
        for file_path in self.output_dir.glob("weekly_report_*.md"):
            # Extract date range from filename: weekly_report_20250825-20250831.md
            filename = file_path.stem
            if filename.startswith("weekly_report_"):
                date_part = filename[14:]  # Remove "weekly_report_"
                if "-" in date_part and len(date_part) == 17:  # YYYYMMDD-YYYYMMDD
                    try:
                        start_str, end_str = date_part.split("-")
                        start_date = datetime.strptime(start_str, "%Y%m%d").date()
                        end_date = datetime.strptime(end_str, "%Y%m%d").date()
                        
                        # Format for display: MM/DD/YYYY - MM/DD/YYYY
                        display_range = f"{start_date.strftime('%m/%d/%Y')} - {end_date.strftime('%m/%d/%Y')}"
                        
                        weeks.append({
                            'display': display_range,
                            'file_path': str(file_path),
                            'start_date': start_date,
                            'end_date': end_date
                        })
                    except ValueError:
                        continue  # Skip invalid filename formats
        
        # Sort by start date, most recent first
        weeks.sort(key=lambda x: x['start_date'], reverse=True)
        return weeks
    
    def generate_last_week_report(self, app_state: AppState) -> str:
        """Generate report for last week"""
        return self.generate_weekly_report(app_state, week_offset=-1)