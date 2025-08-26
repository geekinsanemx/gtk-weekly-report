#!/usr/bin/env python3

import gi
import sys
import os
import signal
from datetime import datetime
from typing import Optional
import subprocess

# Setup for system tray
try:
    gi.require_version('AyatanaAppIndicator3', '0.1')
    gi.require_version('Gtk', '3.0')  # AppIndicator requires GTK3
    from gi.repository import AyatanaAppIndicator3 as AppIndicator3, Gtk, GLib
    APPINDICATOR_AVAILABLE = True
except (ImportError, ValueError):
    try:
        gi.require_version('AppIndicator3', '0.1')
        gi.require_version('Gtk', '3.0')
        from gi.repository import AppIndicator3, Gtk, GLib
        APPINDICATOR_AVAILABLE = True
    except (ImportError, ValueError):
        APPINDICATOR_AVAILABLE = False
        gi.require_version('Notify', '0.7')
        from gi.repository import Notify, GLib

from .data_manager import DataManager
from .notification_manager import NotificationManager, HourlyTimer
from .report_generator import ReportGenerator
from .work_dialog import show_work_entry_dialog


class TrayWeeklyReportDaemon:
    """Weekly Report Daemon with system tray support"""
    
    def __init__(self):
        self.data_manager = DataManager()
        self.notification_manager = NotificationManager()
        self.report_generator = ReportGenerator()
        self.indicator = None
        self.hourly_timer = None
        
        # Check for test mode
        self.test_mode = "--test" in sys.argv
        
        self._setup_signal_handlers()
        
    def _setup_signal_handlers(self):
        """Setup signal handlers"""
        def handler(signum, frame):
            print(f"\\nReceived signal {signum}, shutting down...")
            self.quit()
        
        signal.signal(signal.SIGTERM, handler)
        signal.signal(signal.SIGINT, handler)
    
    def start(self):
        """Start the daemon"""
        print("🚀 Starting Weekly Report Tracker with system tray...")
        
        if APPINDICATOR_AVAILABLE:
            self._setup_system_tray()
        else:
            print("⚠️  AppIndicator not available, running without system tray")
        
        self._setup_timer()
        self._show_startup_notification()
        
        print("✅ Daemon started successfully")
        if self.indicator:
            print("📌 System tray icon should be visible in the notification area")
        
        # Start GTK main loop
        try:
            Gtk.main()
        except KeyboardInterrupt:
            self.quit()
    
    def _setup_system_tray(self):
        """Setup system tray icon"""
        try:
            self.indicator = AppIndicator3.Indicator.new(
                "weekly-report-tracker", 
                "system-users",  # People/worker icon - more recognizable
                AppIndicator3.IndicatorCategory.APPLICATION_STATUS
            )
            
            self.indicator.set_status(AppIndicator3.IndicatorStatus.ACTIVE)
            self.indicator.set_title("Weekly Report Tracker")
            
            # Create menu
            menu = self._create_menu()
            self.indicator.set_menu(menu)
            
            print("✅ System tray icon created")
            
        except Exception as e:
            print(f"❌ Error creating system tray: {e}")
            self.indicator = None
    
    def _create_menu(self):
        """Create system tray menu"""
        menu = Gtk.Menu()
        
        # Current status item
        self.status_item = Gtk.MenuItem(label="📊 Status: Starting...")
        self.status_item.set_sensitive(False)
        menu.append(self.status_item)
        
        # Separator
        menu.append(Gtk.SeparatorMenuItem())
        
        # Add work entry
        add_work_item = Gtk.MenuItem(label="📝 Log Work")
        add_work_item.connect("activate", self._on_add_work)
        menu.append(add_work_item)
        
        # Generate current report
        report_item = Gtk.MenuItem(label="📄 Generate Current Report")
        report_item.connect("activate", self._on_generate_report)
        menu.append(report_item)
        
        # Generate last week report
        last_week_item = Gtk.MenuItem(label="📅 Generate Last Week Report")
        last_week_item.connect("activate", self._on_generate_last_week_report)
        menu.append(last_week_item)
        
        # View Reports submenu
        reports_submenu = self._create_reports_submenu()
        if reports_submenu:
            view_reports_item = Gtk.MenuItem(label="📋 View Reports")
            view_reports_item.set_submenu(reports_submenu)
            menu.append(view_reports_item)
        
        # Show current status
        current_item = Gtk.MenuItem(label="📊 View Status")
        current_item.connect("activate", self._on_show_status)
        menu.append(current_item)
        
        # Separator
        menu.append(Gtk.SeparatorMenuItem())
        
        # Cleanup test data
        cleanup_item = Gtk.MenuItem(label="🧹 Cleanup Test Data")
        cleanup_item.connect("activate", self._on_cleanup_test_data)
        menu.append(cleanup_item)
        
        # Separator
        menu.append(Gtk.SeparatorMenuItem())
        
        # Quit
        quit_item = Gtk.MenuItem(label="🚪 Quit")
        quit_item.connect("activate", self._on_quit)
        menu.append(quit_item)
        
        menu.show_all()
        return menu
    
    def _setup_timer(self):
        """Setup periodic timer"""
        self.hourly_timer = HourlyTimer(self._on_timer_tick)
        
        if self.test_mode:
            print("🧪 Test mode: notifications every 60 seconds")
            self.hourly_timer.start_test_mode(60)  # 1 minute for testing
        else:
            print("⏰ Normal mode: notifications every hour")
            self.hourly_timer.start()
    
    def _show_startup_notification(self):
        """Show startup notification"""
        current_work = self._get_current_work()
        
        if current_work:
            message = f"Working on: {current_work}"
            self._update_tray_status(f"📝 {current_work}")
        else:
            message = "Ready to track work"
            self._update_tray_status("⏸️ No active work")
        
        self.notification_manager.show_info_notification(
            "Weekly Report Tracker",
            f"Iniciado - {message}"
        )
    
    def _on_timer_tick(self):
        """Called by timer"""
        print(f"⏰ Timer tick at {datetime.now().strftime('%H:%M:%S')}")
        
        current_work = self._get_current_work()
        
        self.notification_manager.show_work_check_notification(
            current_work=current_work,
            on_continue=self._on_continue_work,
            on_stop=self._on_stop_work,
            on_details=self._on_add_work_details
        )
    
    def _on_continue_work(self, notification, action, user_data):
        """Continue current work"""
        state = self.data_manager.get_state()
        
        if state.current_ticket and state.current_project:
            self.data_manager.add_work_entry(
                state.current_ticket,
                state.current_project,
                state.current_details or ""
            )
            
            work_desc = f"{state.current_project} - {state.current_ticket}"
            self.notification_manager.show_success_notification(
                f"✅ Time logged: {work_desc}"
            )
            self._update_tray_status(f"📝 {work_desc}")
        else:
            self._on_add_work(None)
    
    def _on_stop_work(self, notification, action, user_data):
        """Stop current work"""
        self.data_manager.stop_current_work()
        self.notification_manager.show_info_notification(
            "⏸️ Work paused",
            "Status updated"
        )
        self._update_tray_status("⏸️ No active work")
    
    def _on_add_work_details(self, notification, action, user_data):
        """Add work details"""
        self._on_add_work(None)
    
    def _on_add_work(self, menuitem):
        """Add new work entry using real dialog"""
        def on_dialog_result(result):
            if result:
                try:
                    # Check if we can auto-detect project
                    auto_project = self.data_manager.get_project_for_ticket(result['ticket'])
                    if auto_project and not result['project']:
                        result['project'] = auto_project
                    
                    # Save work entry
                    self.data_manager.add_work_entry(
                        result['ticket'],
                        result['project'],
                        result['details']
                    )
                    
                    # Update tray status
                    work_desc = f"{result['project']} - {result['ticket']}"
                    self._update_tray_status(f"📝 {work_desc}")
                    
                    # Show success notification
                    self.notification_manager.show_success_notification(
                        f"✅ Work logged: {work_desc}"
                    )
                    
                except Exception as e:
                    self.notification_manager.show_error_notification(
                        f"❌ Error saving work: {str(e)}"
                    )
            else:
                self.notification_manager.show_info_notification(
                    "📝 Entry cancelled",
                    "No work was saved"
                )
        
        # Get current work for pre-filling
        state = self.data_manager.get_state()
        current_ticket = state.current_ticket or ""
        current_project = state.current_project or ""
        
        # Show work entry dialog
        show_work_entry_dialog(
            self.data_manager,
            on_dialog_result,
            current_ticket,
            current_project
        )
    
    def _on_generate_report(self, menuitem):
        """Generate weekly report"""
        try:
            state = self.data_manager.get_state()
            report_path = self.report_generator.generate_weekly_report(state)
            
            # Open report with Pluma
            self._open_with_pluma(report_path)
            
            self.notification_manager.show_success_notification(
                f"📄 Report generated: {os.path.basename(report_path)}"
            )
            
        except Exception as e:
            self.notification_manager.show_error_notification(
                f"❌ Error: {str(e)}"
            )
    
    def _on_generate_last_week_report(self, menuitem):
        """Generate last week report"""
        try:
            state = self.data_manager.get_state()
            report_path = self.report_generator.generate_last_week_report(state)
            
            # Open report with Pluma
            self._open_with_pluma(report_path)
            
            self.notification_manager.show_success_notification(
                f"📅 Last week report generated: {os.path.basename(report_path)}"
            )
            
        except Exception as e:
            self.notification_manager.show_error_notification(
                f"❌ Error generating last week report: {str(e)}"
            )
    
    def _open_with_pluma(self, file_path):
        """Open file with Pluma text editor (non-blocking)"""
        try:
            # Try pluma first (non-blocking)
            try:
                subprocess.Popen(['pluma', file_path], 
                               stdout=subprocess.DEVNULL, 
                               stderr=subprocess.DEVNULL)
                print(f"📄 Opened with pluma: {file_path}")
                return
            except FileNotFoundError:
                pass
            
            # Fallback to gedit (non-blocking)
            try:
                subprocess.Popen(['gedit', file_path],
                               stdout=subprocess.DEVNULL,
                               stderr=subprocess.DEVNULL)
                print(f"📄 Opened with gedit: {file_path}")
                return
            except FileNotFoundError:
                pass
            
            # Final fallback to xdg-open (non-blocking)
            try:
                subprocess.Popen(['xdg-open', file_path],
                               stdout=subprocess.DEVNULL,
                               stderr=subprocess.DEVNULL)
                print(f"📄 Opened with default application: {file_path}")
            except FileNotFoundError:
                print(f"❌ No suitable application found to open: {file_path}")
                
        except Exception as e:
            print(f"❌ Error opening file: {e}")
    
    def _on_show_status(self, menuitem):
        """Show current status"""
        state = self.data_manager.get_state()
        current_work = self._get_current_work()
        
        if current_work:
            message = f"Working on: {current_work}"
            if state.current_details:
                message += f"\nDetails: {state.current_details}"
        else:
            message = "No active work"
        
        # Show summary of this week
        summary = self.data_manager.get_current_week_summary()
        message += f"\n\nThis week: {summary['total_time']/60:.1f}h in {summary['entries_count']} entries"
        
        self.notification_manager.show_info_notification("📊 Current Status", message)
    
    def _create_reports_submenu(self):
        """Create submenu with available weekly reports"""
        weeks = self.report_generator.get_available_weeks()
        if not weeks:
            return None
        
        submenu = Gtk.Menu()
        
        # Limit to last 10 weeks to avoid too long menu
        for week in weeks[:10]:
            week_item = Gtk.MenuItem(label=week['display'])
            week_item.connect("activate", lambda item, path=week['file_path']: self._open_report(path))
            submenu.append(week_item)
        
        # If there are more than 10 weeks, add "More..." option
        if len(weeks) > 10:
            separator = Gtk.SeparatorMenuItem()
            submenu.append(separator)
            
            more_item = Gtk.MenuItem(label="📁 Open Reports Folder")
            more_item.connect("activate", self._on_open_reports_folder)
            submenu.append(more_item)
        
        submenu.show_all()
        return submenu
    
    def _open_report(self, report_path):
        """Open specific report file"""
        self._open_with_pluma(report_path)
        self.notification_manager.show_info_notification(
            "📄 Report opened",
            f"Viewing: {os.path.basename(report_path)}"
        )
    
    def _on_open_reports_folder(self, menuitem):
        """Open reports folder in file manager"""
        try:
            reports_dir = str(self.report_generator.output_dir)
            subprocess.run(['xdg-open', reports_dir], check=False)
            self.notification_manager.show_info_notification(
                "📁 Reports folder opened",
                f"Location: {reports_dir}"
            )
        except Exception as e:
            self.notification_manager.show_error_notification(
                f"❌ Error opening folder: {str(e)}"
            )
    
    def _on_cleanup_test_data(self, menuitem):
        """Cleanup test/demo data"""
        try:
            removed_count = self.data_manager.cleanup_test_data()
            
            if removed_count > 0:
                self.notification_manager.show_success_notification(
                    f"🧹 Test data cleaned up: {removed_count} entries removed"
                )
                # Update tray status
                self._update_tray_status("⚪ No active work")
            else:
                self.notification_manager.show_info_notification(
                    "🧹 No test data found",
                    "Database is already clean"
                )
        except Exception as e:
            self.notification_manager.show_error_notification(
                f"❌ Error during cleanup: {str(e)}"
            )
    
    def _on_quit(self, menuitem):
        """Quit application"""
        self.quit()
    
    def _get_current_work(self) -> Optional[str]:
        """Get current work description"""
        state = self.data_manager.get_state()
        if state.current_ticket and state.current_project:
            return f"{state.current_project} - {state.current_ticket}"
        return None
    
    def _update_tray_status(self, status_text: str):
        """Update tray menu status"""
        if self.indicator and hasattr(self, 'status_item'):
            self.status_item.set_label(status_text)
    
    def cleanup(self):
        """Cleanup resources"""
        print("🧹 Cleaning up daemon resources...")
        
        if self.hourly_timer:
            self.hourly_timer.stop()
            print("  ✅ Timer stopped")
        
        if self.notification_manager:
            self.notification_manager.cleanup()
            print("  ✅ Notifications cleaned up")
        
        # Clean up system tray
        if self.indicator:
            try:
                self.indicator.set_status(AppIndicator3.IndicatorStatus.PASSIVE)
                print("  ✅ System tray icon removed")
            except:
                pass
    
    def quit(self):
        """Quit the application"""
        print("🛑 Shutting down Weekly Report Tracker...")
        self.cleanup()
        Gtk.main_quit()


def cleanup_stale_locks():
    """Clean up stale lock files from previous runs"""
    lock_files = [
        "/tmp/weekly-report-tray.lock",
        "/tmp/weekly-report-tracker.lock",
        "/tmp/weekly-report-tracker-working.lock"
    ]
    
    for lock_file in lock_files:
        if os.path.exists(lock_file):
            try:
                with open(lock_file, 'r') as f:
                    pid = int(f.read().strip())
                
                # Check if process is actually running
                try:
                    os.kill(pid, 0)  # Signal 0 just checks if process exists
                    # Process exists, this is a real running instance
                    return False, f"Process {pid} is running (lock: {lock_file})"
                except ProcessLookupError:
                    # Process doesn't exist, remove stale lock file
                    os.remove(lock_file)
                    print(f"🧹 Removed stale lock file: {lock_file}")
                except PermissionError:
                    # Can't check process (different user), assume it's running
                    return False, f"Cannot verify process {pid} (permission denied)"
                    
            except (ValueError, FileNotFoundError):
                # Invalid or missing lock file, remove it
                try:
                    os.remove(lock_file)
                    print(f"🧹 Removed invalid lock file: {lock_file}")
                except FileNotFoundError:
                    pass
    
    return True, "All stale locks cleaned"

def setup_cleanup_handlers(lock_file):
    """Setup cleanup handlers for graceful shutdown"""
    def cleanup_lock_file():
        try:
            if os.path.exists(lock_file):
                os.remove(lock_file)
                print(f"🧹 Cleaned up lock file: {lock_file}")
        except Exception as e:
            print(f"⚠️  Error cleaning lock file: {e}")
    
    # Register cleanup for normal exit
    import atexit
    atexit.register(cleanup_lock_file)
    
    # Setup signal handlers for graceful shutdown
    def signal_cleanup(signum, frame):
        print(f"\n📡 Received signal {signum}, cleaning up...")
        cleanup_lock_file()
        sys.exit(0)
    
    signal.signal(signal.SIGTERM, signal_cleanup)
    signal.signal(signal.SIGINT, signal_cleanup)

def main():
    """Main entry point with improved lock management"""
    lock_file = "/tmp/weekly-report-tray.lock"
    
    try:
        # First, clean up any stale lock files
        print("🔍 Checking for existing instances...")
        can_start, message = cleanup_stale_locks()
        
        if not can_start:
            print(f"❌ Cannot start: {message}")
            return 1
        
        print("✅ No running instances found")
        
        # Try to create our lock file
        try:
            with open(lock_file, 'x') as f:
                f.write(str(os.getpid()))
            print(f"🔒 Created lock file: {lock_file}")
        except FileExistsError:
            # This shouldn't happen after cleanup, but just in case
            print("❌ Lock file appeared after cleanup - another instance started simultaneously")
            return 1
        
        # Setup cleanup handlers
        setup_cleanup_handlers(lock_file)
        
        # Create and start daemon
        daemon = TrayWeeklyReportDaemon()
        daemon.start()
        return 0
        
    except KeyboardInterrupt:
        print("\n🛑 Interrupted by user")
        return 0
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())