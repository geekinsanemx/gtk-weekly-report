#!/usr/bin/env python3

import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, GLib
from typing import Optional, Callable
import threading


class WorkEntryDialog:
    """GTK3 dialog for entering work information"""
    
    def __init__(self, data_manager, current_ticket: str = "", current_project: str = ""):
        self.data_manager = data_manager
        self.result = None
        self.dialog = None
        self.current_ticket = current_ticket
        self.current_project = current_project
        
        # Get existing tickets for combobox
        self.existing_tickets = self._get_existing_tickets()
        
        # Create dialog in main thread
        GLib.idle_add(self._create_dialog)
    
    def _get_existing_tickets(self):
        """Get list of existing tickets from work entries"""
        state = self.data_manager.get_state()
        tickets = {}
        
        for entry in state.work_entries:
            if entry.ticket not in tickets:
                tickets[entry.ticket] = {
                    'project': entry.project,
                    'last_details': entry.details
                }
        
        return tickets
    
    def _create_dialog(self):
        """Create work entry dialog"""
        self.dialog = Gtk.Dialog(
            title="📝 Log Work Entry",
            flags=Gtk.DialogFlags.MODAL
        )
        
        self.dialog.set_default_size(450, 350)
        self.dialog.set_position(Gtk.WindowPosition.CENTER)
        
        # Add buttons
        self.dialog.add_button("Cancel", Gtk.ResponseType.CANCEL)
        save_button = self.dialog.add_button("✅ Save", Gtk.ResponseType.OK)
        save_button.get_style_context().add_class("suggested-action")
        
        # Create content
        content_area = self.dialog.get_content_area()
        content_area.set_border_width(20)
        content_area.set_spacing(15)
        
        # Header
        header = Gtk.Label()
        header.set_markup("<big><b>Log work activity</b></big>")
        header.set_halign(Gtk.Align.START)
        content_area.pack_start(header, False, False, 0)
        
        # Ticket entry with combobox
        ticket_frame = Gtk.Frame(label="🎫 Ticket Number")
        ticket_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=5)
        ticket_box.set_border_width(10)
        
        # Create combobox with text entry capability
        self.ticket_combo = Gtk.ComboBoxText.new_with_entry()
        self.ticket_combo.set_entry_text_column(0)
        
        # Add existing tickets to combobox
        for ticket in sorted(self.existing_tickets.keys()):
            self.ticket_combo.append_text(ticket)
        
        # Set current ticket if provided
        if self.current_ticket:
            self.ticket_combo.get_child().set_text(self.current_ticket)
        else:
            self.ticket_combo.get_child().set_placeholder_text("Ex: PROJ-123, BUG-456, TASK-789...")
        
        ticket_box.pack_start(self.ticket_combo, False, False, 0)
        ticket_frame.add(ticket_box)
        content_area.pack_start(ticket_frame, False, False, 0)
        
        # Project entry
        project_frame = Gtk.Frame(label="📁 Project")
        project_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=5)
        project_box.set_border_width(10)
        
        self.project_entry = Gtk.Entry()
        self.project_entry.set_placeholder_text("Project name...")
        if self.current_project:
            self.project_entry.set_text(self.current_project)
        
        # Auto-complete hint
        self.project_hint = Gtk.Label()
        self.project_hint.set_halign(Gtk.Align.START)
        
        project_box.pack_start(self.project_entry, False, False, 0)
        project_box.pack_start(self.project_hint, False, False, 0)
        project_frame.add(project_box)
        content_area.pack_start(project_frame, False, False, 0)
        
        # Details entry
        details_frame = Gtk.Frame(label="📋 Details (optional)")
        details_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=5)
        details_box.set_border_width(10)
        
        scrolled = Gtk.ScrolledWindow()
        scrolled.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
        scrolled.set_min_content_height(80)
        scrolled.set_shadow_type(Gtk.ShadowType.IN)
        
        self.details_textview = Gtk.TextView()
        self.details_textview.set_wrap_mode(Gtk.WrapMode.WORD)
        self.details_textview.set_left_margin(8)
        self.details_textview.set_right_margin(8)
        
        # Start with empty details - use placeholder attribute instead
        buffer = self.details_textview.get_buffer()
        buffer.set_text("")  # Always start empty
        
        # Add placeholder text using buffer tags for better UX
        self._setup_placeholder_text()
        
        scrolled.add(self.details_textview)
        details_box.pack_start(scrolled, True, True, 0)
        details_frame.add(details_box)
        content_area.pack_start(details_frame, True, True, 0)
        
        # Connect signals
        self.ticket_combo.connect("changed", self._on_ticket_changed)
        self.ticket_combo.get_child().connect("changed", self._on_ticket_text_changed)
        
        # Connect focus events for placeholder text
        self.details_textview.connect("focus-in-event", self._on_details_focus_in)
        self.details_textview.connect("focus-out-event", self._on_details_focus_out)
        buffer.connect("changed", self._on_details_changed)
        
        # Focus on ticket entry
        self.ticket_combo.grab_focus()
        
        content_area.show_all()
        return False
    
    def _setup_placeholder_text(self):
        """Setup placeholder text for details field"""
        self.placeholder_text = "Describe what you're working on: implementation, testing, debugging, meeting..."
        self.showing_placeholder = False
        self._update_placeholder_visibility()
    
    def _update_placeholder_visibility(self):
        """Update placeholder text visibility based on content"""
        buffer = self.details_textview.get_buffer()
        text = buffer.get_text(buffer.get_start_iter(), buffer.get_end_iter(), False)
        
        if not text.strip():
            # Show placeholder
            self.showing_placeholder = True
            buffer.set_text(self.placeholder_text)
            # Make text look like placeholder (gray)
            buffer.apply_tag(self._get_placeholder_tag(), 
                           buffer.get_start_iter(), 
                           buffer.get_end_iter())
        else:
            self.showing_placeholder = False
    
    def _get_placeholder_tag(self):
        """Get or create placeholder text tag"""
        buffer = self.details_textview.get_buffer()
        tag = buffer.get_tag_table().lookup("placeholder")
        if not tag:
            tag = buffer.create_tag("placeholder", foreground="gray", style="italic")
        return tag
    
    def _on_details_focus_in(self, textview, event):
        """Handle focus in - remove placeholder if showing"""
        if self.showing_placeholder:
            buffer = textview.get_buffer()
            buffer.set_text("")
            self.showing_placeholder = False
        return False
    
    def _on_details_focus_out(self, textview, event):
        """Handle focus out - add placeholder if empty"""
        self._update_placeholder_visibility()
        return False
    
    def _on_details_changed(self, buffer):
        """Handle text changes in details field"""
        if self.showing_placeholder:
            return  # Don't process changes while showing placeholder
        
        text = buffer.get_text(buffer.get_start_iter(), buffer.get_end_iter(), False)
        if not text.strip() and not self.showing_placeholder:
            # Text was cleared, will show placeholder on focus out
            pass
    
    def _on_ticket_changed(self, combo):
        """Handle ticket selection from combobox"""
        active_text = combo.get_active_text()
        if active_text and active_text in self.existing_tickets:
            # Auto-fill project from existing ticket
            existing_data = self.existing_tickets[active_text]
            self.project_entry.set_text(existing_data['project'])
            self.project_hint.set_markup(f"<small><span color='green'>✅ Auto-filled from existing ticket</span></small>")
            
            # Do NOT auto-fill details - keep empty for new entry
            # User specifically requested details to always be empty
            buffer = self.details_textview.get_buffer()
            buffer.set_text("")  # Always start empty
            self._update_placeholder_visibility()
    
    def _on_ticket_text_changed(self, entry):
        """Handle manual ticket text entry"""
        ticket = entry.get_text().strip()
        if ticket and len(ticket) > 2:
            # Try to auto-detect project
            auto_project = self.data_manager.get_project_for_ticket(ticket)
            if auto_project and not self.project_entry.get_text():
                self.project_entry.set_text(auto_project)
                self.project_hint.set_markup(f"<small><span color='green'>✅ Auto-detected: {auto_project}</span></small>")
            elif ticket not in self.existing_tickets:
                # Show hint for new ticket
                prefix = ticket.split('-')[0] if '-' in ticket else ticket[:3].upper()
                self.project_hint.set_markup(f"<small><i>New project for: {prefix}</i></small>")
    
    def run_async(self, callback: Callable):
        """Run dialog asynchronously and call callback with result"""
        def dialog_thread():
            # Wait for dialog to be created
            while self.dialog is None:
                GLib.usleep(10000)  # 10ms
            
            GLib.idle_add(self._show_and_wait, callback)
        
        thread = threading.Thread(target=dialog_thread, daemon=True)
        thread.start()
    
    def _show_and_wait(self, callback):
        """Show dialog and handle response"""
        response = self.dialog.run()
        
        result = None
        if response == Gtk.ResponseType.OK:
            ticket = self.ticket_combo.get_child().get_text().strip()
            project = self.project_entry.get_text().strip()
            
            if ticket and project:
                # Get details from text view
                buffer = self.details_textview.get_buffer()
                start_iter = buffer.get_start_iter()
                end_iter = buffer.get_end_iter()
                details = buffer.get_text(start_iter, end_iter, False).strip()
                
                # Don't save placeholder text
                if self.showing_placeholder or details == self.placeholder_text:
                    details = ""
                
                result = {
                    'ticket': ticket,
                    'project': project,
                    'details': details
                }
            else:
                # Show error and try again
                self._show_error("❌ Error: Ticket and Project are required fields")
                self.dialog.destroy()
                GLib.idle_add(self._create_dialog)
                GLib.timeout_add(100, lambda: self._show_and_wait(callback))
                return False
        
        self.dialog.destroy()
        callback(result)
        return False
    
    def _show_error(self, message):
        """Show error message"""
        error_dialog = Gtk.MessageDialog(
            parent=self.dialog,
            flags=Gtk.DialogFlags.MODAL,
            message_type=Gtk.MessageType.ERROR,
            buttons=Gtk.ButtonsType.OK,
            text=message
        )
        error_dialog.run()
        error_dialog.destroy()


def show_work_entry_dialog(data_manager, callback, current_ticket="", current_project=""):
    """Convenience function to show work entry dialog"""
    dialog = WorkEntryDialog(data_manager, current_ticket, current_project)
    dialog.run_async(callback)