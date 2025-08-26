import gi
gi.require_version('Notify', '0.7')
from gi.repository import Notify, GLib
from typing import Callable, Optional


class NotificationManager:
    def __init__(self):
        Notify.init("Weekly Report Tracker")
        self.current_notification: Optional[Notify.Notification] = None
        
    def show_work_check_notification(self, current_work: Optional[str], 
                                   on_continue: Callable, 
                                   on_stop: Callable, 
                                   on_details: Callable) -> None:
        """Show notification asking if user is still working"""
        self._close_current_notification()
        
        if current_work:
            title = "⏰ Still working?"
            message = f"Working on: {current_work}"
            icon = "appointment-soon"  # Clock icon
            
            notification = Notify.Notification.new(title, message, icon)
            
            # Add action buttons with icons
            notification.add_action("continue", "✅ Yes", on_continue, None)
            notification.add_action("stop", "🔴 No", on_stop, None) 
            notification.add_action("details", "📝 +Details", on_details, None)
        else:
            title = "📝 Work Report"
            message = "Want to report what you're working on?"
            icon = "dialog-question"
            
            notification = Notify.Notification.new(title, message, icon)
            
            # Add action buttons with icons
            notification.add_action("yes", "✅ Yes", on_continue, None)
            notification.add_action("no", "🔴 No", on_stop, None)
        
        # Set notification properties
        notification.set_timeout(30000)  # 30 seconds timeout
        notification.set_urgency(Notify.Urgency.NORMAL)
        
        self.current_notification = notification
        
        try:
            notification.show()
        except Exception as e:
            print(f"Error showing notification: {e}")
    
    def show_info_notification(self, title: str, message: str) -> None:
        """Show simple info notification"""
        self._close_current_notification()
        
        notification = Notify.Notification.new(title, message, "dialog-information")
        notification.set_timeout(5000)  # 5 seconds
        notification.set_urgency(Notify.Urgency.LOW)
        
        try:
            notification.show()
        except Exception as e:
            print(f"Error showing notification: {e}")
    
    def show_success_notification(self, message: str) -> None:
        """Show success notification"""
        self.show_info_notification("Trabajo registrado", message)
    
    def show_error_notification(self, message: str) -> None:
        """Show error notification"""
        self._close_current_notification()
        
        notification = Notify.Notification.new("Error", message, "dialog-error")
        notification.set_timeout(8000)  # 8 seconds
        notification.set_urgency(Notify.Urgency.CRITICAL)
        
        try:
            notification.show()
        except Exception as e:
            print(f"Error showing error notification: {e}")
    
    def show_report_ready_notification(self, report_path: str, on_open: Callable) -> None:
        """Show notification when weekly report is ready"""
        self._close_current_notification()
        
        title = "Reporte semanal generado"
        message = f"Tu reporte está listo: {report_path}"
        
        notification = Notify.Notification.new(title, message, "document-new")
        notification.add_action("open", "Abrir", on_open, None)
        notification.set_timeout(15000)  # 15 seconds
        notification.set_urgency(Notify.Urgency.NORMAL)
        
        try:
            notification.show()
        except Exception as e:
            print(f"Error showing report notification: {e}")
    
    def _close_current_notification(self) -> None:
        """Close current notification if exists"""
        if self.current_notification:
            try:
                self.current_notification.close()
            except Exception:
                pass  # Notification might already be closed
            self.current_notification = None
    
    def cleanup(self) -> None:
        """Cleanup notifications"""
        self._close_current_notification()
        Notify.uninit()


class HourlyTimer:
    """Timer to trigger hourly work checks"""
    
    def __init__(self, callback: Callable):
        self.callback = callback
        self.timer_id: Optional[int] = None
    
    def start(self) -> None:
        """Start hourly timer"""
        if self.timer_id:
            self.stop()
        
        # Timer for every hour (3600 seconds)
        # For testing, you can change to smaller interval like 300 (5 minutes)
        self.timer_id = GLib.timeout_add_seconds(3600, self._on_timer)
        print("Hourly timer started")
    
    def start_test_mode(self, interval_seconds: int = 300) -> None:
        """Start timer with custom interval for testing"""
        if self.timer_id:
            self.stop()
        
        self.timer_id = GLib.timeout_add_seconds(interval_seconds, self._on_timer)
        print(f"Timer started in test mode: {interval_seconds} seconds interval")
    
    def stop(self) -> None:
        """Stop hourly timer"""
        if self.timer_id:
            GLib.source_remove(self.timer_id)
            self.timer_id = None
            print("Timer stopped")
    
    def _on_timer(self) -> bool:
        """Timer callback - returns True to continue timer"""
        try:
            self.callback()
            return True  # Continue timer
        except Exception as e:
            print(f"Error in timer callback: {e}")
            return True  # Continue timer even on error