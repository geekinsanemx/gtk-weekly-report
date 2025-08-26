#!/bin/bash
# Uninstall script for Weekly Report Tracker

set -e

echo "🗑️  Uninstalling Weekly Report Tracker..."
echo "========================================"

APP_DIR="$HOME/.local/share/weekly-report-tracker"
DATA_DIR="$HOME/.weekly-report-tracker"
AUTOSTART_FILE="$HOME/.config/autostart/weekly-report-tracker.desktop"
APP_DESKTOP_FILE="$HOME/.local/share/applications/weekly-report-tracker.desktop"

# Stop running instances
echo "🛑 Stopping running instances..."
pkill -f "weekly_report" || true
pkill -f "weekly-report" || true

# Remove symlinks
echo "🔗 Removing command shortcuts..."
rm -f "$HOME/.local/bin/weekly-report"
rm -f "$HOME/.local/bin/weekly-status"

# Remove application files
echo "📋 Removing application files..."
if [ -d "$APP_DIR" ]; then
    rm -rf "$APP_DIR"
    echo "   ✅ Removed: $APP_DIR"
else
    echo "   ℹ️  Application directory not found: $APP_DIR"
fi

# Remove autostart file
echo "🔧 Removing autostart configuration..."
if [ -f "$AUTOSTART_FILE" ]; then
    rm "$AUTOSTART_FILE"
    echo "   ✅ Removed: $AUTOSTART_FILE"
else
    echo "   ℹ️  Autostart file not found: $AUTOSTART_FILE"
fi

# Remove desktop application entry
echo "🖥️  Removing desktop application entry..."
if [ -f "$APP_DESKTOP_FILE" ]; then
    rm "$APP_DESKTOP_FILE"
    echo "   ✅ Removed: $APP_DESKTOP_FILE"
else
    echo "   ℹ️  Desktop file not found: $APP_DESKTOP_FILE"
fi

# Ask about data directory
echo ""
echo "💾 Data directory contains your work reports and entries:"
echo "   $DATA_DIR"
echo ""
echo "Do you want to remove your data as well? [y/N]"
read -r response
if [[ "$response" =~ ^([yY][eE][sS]|[yY])$ ]]; then
    if [ -d "$DATA_DIR" ]; then
        rm -rf "$DATA_DIR"
        echo "   ✅ Removed data directory: $DATA_DIR"
    else
        echo "   ℹ️  Data directory not found: $DATA_DIR"
    fi
else
    echo "   📁 Kept data directory: $DATA_DIR"
    echo "   Your work reports and entries are preserved."
fi

echo ""
echo "✅ Uninstallation completed!"
echo "=========================="
echo ""
echo "📊 Weekly Report Tracker has been removed from your system."
echo ""
if [[ ! "$response" =~ ^([yY][eE][sS]|[yY])$ ]]; then
    echo "💡 Your data is still available at: $DATA_DIR"
    echo "   You can reinstall the application later to access it."
    echo ""
fi
echo "🙏 Thank you for using Weekly Report Tracker!"