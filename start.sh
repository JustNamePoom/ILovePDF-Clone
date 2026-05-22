#!/bin/bash
# ─── iLovePDF Local Clone – Setup & Run ───────────────────────────────────────
set -e

echo ""
echo "  ❤️  iLovePDF Local Clone – Setup"
echo "  ─────────────────────────────────"

# 1. Python deps
echo ""
echo "  📦 Installing Python dependencies..."
pip install flask flask-cors pikepdf Pillow img2pdf reportlab PyMuPDF --break-system-packages -q

# 2. Optional: LibreOffice (for Word/Excel → PDF)
if command -v libreoffice &>/dev/null; then
  echo "  ✅ LibreOffice found (Word/Excel conversion available)"
else
  echo "  ⚠️  LibreOffice not found. Word/Excel → PDF will not work."
  echo "     Install with: sudo apt install libreoffice"
fi

echo ""
echo "  ✅ Ready! Starting server on http://0.0.0.0:5000"
echo "  🌐 Access from any device on your local network:"

# Print all LAN IPs
python3 -c "
import socket, subprocess
try:
    result = subprocess.run(['hostname', '-I'], capture_output=True, text=True)
    ips = result.stdout.strip().split()
    for ip in ips:
        print(f'     → http://{ip}:5000')
except:
    pass
print('     → http://localhost:5000')
"

echo ""
echo "  Press Ctrl+C to stop."
echo ""

cd "$(dirname "$0")"
python3 app.py
