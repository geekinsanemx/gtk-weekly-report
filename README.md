# Weekly Report Tracker

A GTK application for GNOME Linux that helps you track work activities and automatically generate weekly reports.

## ✨ Features

- 📅 **Automatic tracking**: Hourly notifications asking what you're working on
- 🔔 **Non-intrusive notifications**: Using libnotify with interactive buttons
- 🏷️ **Auto-project recognition**: Automatically maps tickets to known projects  
- 📊 **Weekly reports**: Generates reports in Markdown format organized by project
- 🖥️ **Background daemon**: Runs invisibly with system tray icon
- 💾 **Automatic persistence**: Saves all your work automatically in `~/.weekly-report-tracker`
- 📝 **Multiple report types**: Current week and last week report generation
- 🧹 **Test data cleanup**: Automatic cleanup of demo/test entries

## 🚀 Quick Installation

```bash
git clone <repository-url>
cd gtk-weekly-report
./install.sh
```

The installation script:
- Installs system dependencies (Ubuntu/Debian/Fedora/Arch)
- Sets up autostart for automatic startup
- Creates convenient command shortcuts
- Sets up persistent data directories
- Makes all necessary files executable

## 📋 System Requirements

### Supported Distributions
- Ubuntu/Debian (apt)
- Fedora (dnf) 
- Arch Linux (pacman)
- Other distributions (manual dependency installation)

### Dependencies
- Python 3
- PyGObject (python3-gi)
- GTK 3
- libnotify 
- libappindicator3
- Pluma text editor (recommended)

## 🎯 Usage

### After Installation
The application will:
- Start automatically on login
- Run in background with system tray icon (user/people icon)
- Show hourly notifications asking about work status
- Generate reports accessible via system tray menu

### Command Line Usage
```bash
# Start application
weekly-report

# Test mode (notifications every 60 seconds)
weekly-report --test  

# Check status
weekly-status status

# Generate current week report
weekly-status report

# Generate last week report  
weekly-status lastweek

# Add sample work entry (testing)
weekly-status add

# Clean up test data
weekly-status cleanup
```

## 📊 System Tray Menu

Right-click the system tray icon for:
- 📝 **Log Work** - Add new work entry
- 📄 **Generate Current Report** - Create this week's report
- 📅 **Generate Last Week Report** - Create last week's report
- 📋 **View Reports** - Browse historical reports
- 📊 **View Status** - Show current work status
- 🧹 **Cleanup Test Data** - Remove demo entries

## 💾 Data Storage

- **Application files**: `~/.local/share/weekly-report-tracker/`
- **Work data**: `~/.weekly-report-tracker/database.json`
- **Reports**: `~/.weekly-report-tracker/reports/`
- **Autostart**: `~/.config/autostart/weekly-report-tracker.desktop`

## 🔧 Work Entry Dialog

When logging work, you can:
- Enter ticket number (e.g., PROJ-123, BUG-456)
- Select existing tickets from dropdown (auto-fills project)
- Specify project name
- Add optional details about work performed
- All fields start clean for new entries

## 📋 Report Format

Reports are generated in clean Markdown format:
```markdown
# Weekly Report
**Week:** MM/DD/YYYY - MM/DD/YYYY

---

## Executive Summary
- **Total hours worked:** X.X hours
- **Total entries:** X
- **Projects worked on:** X

---

## Project Name
**Total time:** X.X hours

### TICKET-123
**Time spent:** X.X hours
**Sessions:** X

**Activities:**
- Activity description

## Daily Breakdown
[Day-by-day breakdown of activities]

---
```

## 🗑️ Uninstallation

```bash
./uninstall.sh
```

The uninstall script will:
- Stop running application instances
- Remove application files
- Remove autostart configuration
- Optionally preserve or remove your work data

## 🧪 Development & Testing

```bash
# Test mode for faster notifications
./weekly_report --test

# Check syntax of scripts
bash -n install.sh
bash -n uninstall.sh

# Manual cleanup of test data
./check_status.py cleanup
```

## 📁 Project Structure

```
gtk-weekly-report/
├── src/                    # Application source code
│   ├── tray_daemon.py     # Main daemon with system tray
│   ├── data_manager.py    # Data persistence layer
│   ├── report_generator.py # Report generation
│   ├── work_dialog.py     # Work entry dialog
│   └── models.py          # Data models
├── weekly_report          # Main executable
├── check_status.py        # Status and utility script
├── install.sh             # Installation script
├── uninstall.sh           # Uninstallation script
└── README.md              # This file
```

## 🤝 Contributing

This is a personal productivity tool. Feel free to fork and adapt for your needs!

## 📄 License

MIT License - Feel free to use and modify as needed.

---

**Note**: This application is designed for GNOME desktop environments with system tray support. It may work on other desktop environments but is optimized for GNOME.