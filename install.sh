#!/bin/bash
# Installation script for Weekly Report Tracker
# Supports Ubuntu/Debian and other Linux distributions

set -e

echo "🚀 Installing Weekly Report Tracker..."
echo "======================================"

# Get current directory (where the script is located)
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
APP_DIR="$HOME/.local/share/weekly-report-tracker"

echo "📁 Script directory: $SCRIPT_DIR"
echo "📁 Installation directory: $APP_DIR"

# Check if main executable exists
if [ ! -f "$SCRIPT_DIR/weekly_report" ]; then
    echo "❌ Error: weekly_report executable not found!"
    echo "   Make sure you're running this from the project directory."
    exit 1
fi

# Install system dependencies
echo ""
echo "📦 Installing system dependencies..."
if command -v apt-get &> /dev/null; then
    echo "   Detected Ubuntu/Debian system"
    sudo apt-get update
    sudo apt-get install -y \
        python3 \
        python3-gi \
        python3-gi-cairo \
        gir1.2-gtk-3.0 \
        gir1.2-notify-0.7 \
        gir1.2-appindicator3-0.1 \
        libappindicator3-dev \
        pluma
elif command -v dnf &> /dev/null; then
    echo "   Detected Fedora system"
    sudo dnf install -y \
        python3 \
        python3-gobject \
        gtk3-devel \
        libnotify-devel \
        libappindicator-gtk3-devel \
        pluma
elif command -v pacman &> /dev/null; then
    echo "   Detected Arch Linux system"
    sudo pacman -S --needed \
        python \
        python-gobject \
        gtk3 \
        libnotify \
        libappindicator-gtk3 \
        pluma
else
    echo "⚠️  Warning: Unknown package manager. Please install these dependencies manually:"
    echo "   - Python 3"
    echo "   - python3-gi (PyGObject)"
    echo "   - GTK 3"
    echo "   - libnotify"
    echo "   - libappindicator3"
    echo "   - pluma text editor (optional)"
fi

# Create application directory
echo ""
echo "📁 Creating application directory..."
mkdir -p "$APP_DIR"

# Copy application files
echo "📋 Copying application files..."
cp -r "$SCRIPT_DIR/src" "$APP_DIR/"
cp "$SCRIPT_DIR/weekly_report" "$APP_DIR/"
cp "$SCRIPT_DIR/check_status.py" "$APP_DIR/"

# Make executables
chmod +x "$APP_DIR/weekly_report"
chmod +x "$APP_DIR/check_status.py"

# Create persistent data directory
echo "💾 Setting up data directory..."
mkdir -p "$HOME/.weekly-report-tracker"
mkdir -p "$HOME/.weekly-report-tracker/reports"

# Create autostart directory if it doesn't exist
echo "🔧 Setting up autostart..."
AUTOSTART_DIR="$HOME/.config/autostart"
mkdir -p "$AUTOSTART_DIR"

# Create desktop file for autostart
DESKTOP_FILE="$AUTOSTART_DIR/weekly-report-tracker.desktop"
cat > "$DESKTOP_FILE" << EOF
[Desktop Entry]
Type=Application
Name=Weekly Report Tracker
Comment=Track work activities and generate weekly reports
Exec=$APP_DIR/weekly_report
Icon=system-users
Terminal=false
NoDisplay=true
X-GNOME-Autostart-enabled=true
X-GNOME-Autostart-Delay=10
StartupNotify=false
Categories=Office;ProjectManagement;
EOF

chmod +x "$DESKTOP_FILE"

# Create convenient symlinks in user's bin directory
echo "🔗 Creating command shortcuts..."
mkdir -p "$HOME/.local/bin"
ln -sf "$APP_DIR/weekly_report" "$HOME/.local/bin/weekly-report"
ln -sf "$APP_DIR/check_status.py" "$HOME/.local/bin/weekly-status"

# Add ~/.local/bin to PATH if not already there
if [[ ":$PATH:" != *":$HOME/.local/bin:"* ]]; then
    echo ""
    echo "💡 Adding ~/.local/bin to PATH..."
    echo 'export PATH="$HOME/.local/bin:$PATH"' >> "$HOME/.bashrc"
    echo "   Note: You may need to restart your terminal or run:"
    echo "   source ~/.bashrc"
fi

# Create desktop application entry
echo "🖥️  Creating desktop application entry..."
DESKTOP_APPS_DIR="$HOME/.local/share/applications"
mkdir -p "$DESKTOP_APPS_DIR"
APP_DESKTOP_FILE="$DESKTOP_APPS_DIR/weekly-report-tracker.desktop"
cat > "$APP_DESKTOP_FILE" << EOF
[Desktop Entry]
Version=1.0
Type=Application
Name=Weekly Report Tracker
Comment=Track work activities and generate weekly reports
Exec=$APP_DIR/weekly_report
Icon=system-users
Terminal=false
Categories=Office;ProjectManagement;Development;
Keywords=report;work;tracking;productivity;
EOF

chmod +x "$APP_DESKTOP_FILE"

echo ""
echo "✅ Installation completed successfully!"
echo "======================================"
echo ""
echo "📊 Weekly Report Tracker is now installed!"
echo ""
echo "🚀 Usage:"
echo "   • The application will start automatically on next login"
echo "   • To start now: weekly-report (or $APP_DIR/weekly_report)"
echo "   • Check status: weekly-status (or $APP_DIR/check_status.py)"
echo "   • Test mode: weekly-report --test"
echo ""
echo "📁 Files installed to:"
echo "   • Application: $APP_DIR"
echo "   • Data: $HOME/.weekly-report-tracker"
echo "   • Autostart: $AUTOSTART_DIR/weekly-report-tracker.desktop"
echo ""
echo "🎯 The application will run in the background with a system tray icon."
echo "   Look for the user/people icon in your notification area."
echo ""
echo "🧹 To uninstall, delete these directories:"
echo "   • $APP_DIR"
echo "   • $HOME/.weekly-report-tracker (contains your data!)"
echo "   • $AUTOSTART_DIR/weekly-report-tracker.desktop"
echo ""

# Offer to start the application now
echo "Would you like to start the application now? [y/N]"
read -r response
if [[ "$response" =~ ^([yY][eE][sS]|[yY])$ ]]; then
    echo "🚀 Starting Weekly Report Tracker..."
    "$APP_DIR/weekly_report" &
    echo "✅ Application started! Look for the system tray icon."
else
    echo "👍 Application will start automatically on your next login."
fi

echo ""
echo "🎉 Setup complete! Enjoy tracking your work activities!"