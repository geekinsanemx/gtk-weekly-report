#!/usr/bin/env python3
"""
Check Weekly Report Tracker status and perform basic operations
"""

import sys
import os
import subprocess

# Add src directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def check_running():
    """Check if daemon is running (with automatic stale lock cleanup)"""
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
                    return True, pid, lock_file
                except ProcessLookupError:
                    # Process doesn't exist, remove stale lock file
                    os.remove(lock_file)
                    print(f"🧹 Removed stale lock file: {lock_file}")
            except (ValueError, FileNotFoundError):
                try:
                    os.remove(lock_file)
                    print(f"🧹 Removed invalid lock file: {lock_file}")
                except FileNotFoundError:
                    pass
    
    return False, None, None

def show_status():
    """Show current status"""
    from src.data_manager import DataManager
    from src.report_generator import ReportGenerator
    
    print("📊 Weekly Report Tracker - Status")
    print("=" * 40)
    
    # Check if daemon is running
    running, pid, lock_file = check_running()
    if running:
        print(f"🟢 Status: RUNNING (PID: {pid})")
        print(f"🔒 Lock file: {lock_file}")
    else:
        print("🔴 Status: NOT RUNNING")
    
    # Check data
    try:
        dm = DataManager()
        state = dm.get_state()
        
        print(f"\n📝 Current Work:")
        if state.current_ticket and state.current_project:
            print(f"   Project: {state.current_project}")
            print(f"   Ticket: {state.current_ticket}")
            if state.current_details:
                print(f"   Details: {state.current_details}")
        else:
            print("   No active work")
        
        print(f"\n📈 This Week Summary:")
        summary = dm.get_current_week_summary()
        print(f"   Total hours: {summary['total_time']/60:.1f}")
        print(f"   Entries: {summary['entries_count']}")
        print(f"   Projects: {len(summary['projects'])}")
        
        for project, data in summary['projects'].items():
            print(f"     • {project}: {data['time']/60:.1f}h")
        
        # Show data location
        print(f"\n📁 Data location: {dm.get_data_location()}")
        
    except Exception as e:
        print(f"❌ Error reading data: {e}")

def generate_report():
    """Generate current report"""
    try:
        from src.data_manager import DataManager
        from src.report_generator import ReportGenerator
        
        print("📄 Generating weekly report...")
        dm = DataManager()
        rg = ReportGenerator()
        
        report_path = rg.generate_weekly_report(dm.get_state())
        print(f"✅ Report generated: {report_path}")
        
        # Open report with Pluma (non-blocking)
        try:
            # Try pluma first
            try:
                subprocess.Popen(['pluma', report_path], 
                               stdout=subprocess.DEVNULL, 
                               stderr=subprocess.DEVNULL)
                print(f"📄 Opened with pluma")
            except FileNotFoundError:
                # Fallback to gedit
                try:
                    subprocess.Popen(['gedit', report_path],
                                   stdout=subprocess.DEVNULL,
                                   stderr=subprocess.DEVNULL)
                    print(f"📄 Opened with gedit")
                except FileNotFoundError:
                    # Final fallback to xdg-open
                    subprocess.Popen(['xdg-open', report_path],
                                   stdout=subprocess.DEVNULL,
                                   stderr=subprocess.DEVNULL)
                    print(f"📄 Opened with default application")
        except Exception as e:
            print(f"❌ Error opening file: {e}")
        
    except Exception as e:
        print(f"❌ Error generating report: {e}")

def generate_last_week_report():
    """Generate last week report"""
    try:
        from src.data_manager import DataManager
        from src.report_generator import ReportGenerator
        
        print("📅 Generating last week report...")
        dm = DataManager()
        rg = ReportGenerator()
        
        report_path = rg.generate_last_week_report(dm.get_state())
        print(f"✅ Last week report generated: {report_path}")
        
        # Open report with Pluma (non-blocking)
        try:
            # Try pluma first
            try:
                subprocess.Popen(['pluma', report_path], 
                               stdout=subprocess.DEVNULL, 
                               stderr=subprocess.DEVNULL)
                print(f"📄 Opened with pluma")
            except FileNotFoundError:
                # Fallback to gedit
                try:
                    subprocess.Popen(['gedit', report_path],
                                   stdout=subprocess.DEVNULL,
                                   stderr=subprocess.DEVNULL)
                    print(f"📄 Opened with gedit")
                except FileNotFoundError:
                    # Final fallback to xdg-open
                    subprocess.Popen(['xdg-open', report_path],
                                   stdout=subprocess.DEVNULL,
                                   stderr=subprocess.DEVNULL)
                    print(f"📄 Opened with default application")
        except Exception as e:
            print(f"❌ Error opening file: {e}")
        
    except Exception as e:
        print(f"❌ Error generating last week report: {e}")

def add_sample_work():
    """Add sample work entry (FOR TESTING ONLY)"""
    try:
        from src.data_manager import DataManager
        
        dm = DataManager()
        dm.add_work_entry("TEST-123", "Test Project", "Sample entry added via script")
        print("✅ Sample work entry added (FOR TESTING - run cleanup to remove)")
        
    except Exception as e:
        print(f"❌ Error adding work: {e}")

def cleanup_test_data():
    """Cleanup test/demo data"""
    try:
        from src.data_manager import DataManager
        
        dm = DataManager()
        removed_count = dm.cleanup_test_data()
        
        if removed_count > 0:
            print(f"🧹 Cleaned up {removed_count} test entries")
        else:
            print("🧹 No test data found - database is clean")
        
    except Exception as e:
        print(f"❌ Error during cleanup: {e}")

def main():
    if len(sys.argv) > 1:
        command = sys.argv[1].lower()
        
        if command == "status":
            show_status()
        elif command == "report":
            generate_report()
        elif command == "lastweek":
            generate_last_week_report()
        elif command == "add":
            add_sample_work()
        elif command == "cleanup":
            cleanup_test_data()
        elif command == "start":
            if not check_running()[0]:
                print("🚀 Starting Weekly Report Tracker...")
                subprocess.Popen(['./weekly_report'])
                print("✅ Started (running in background)")
            else:
                print("⚠️  Already running")
        elif command == "stop":
            running, pid, lock_file = check_running()
            if running:
                os.kill(pid, 15)  # SIGTERM
                print("🛑 Sent stop signal")
            else:
                print("⚠️  Not running")
        else:
            print("Unknown command. Use: status, report, lastweek, add, cleanup, start, stop")
    else:
        show_status()

if __name__ == "__main__":
    main()