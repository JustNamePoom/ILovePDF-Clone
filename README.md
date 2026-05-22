# ❤️ iLovePDF Local Clone

A full iLovePDF-style PDF tool website you can run on your local network.  
No internet required. Works for everyone on the same WiFi/LAN.

---

## 🚀 Quick Start

### 1. Install & Run

```bash
chmod +x start.sh
./start.sh
```

Or manually:

```bash
pip install flask flask-cors pikepdf Pillow img2pdf reportlab PyMuPDF
python3 app.py
```

### 2. Open in browser

The terminal will show your local IP, e.g.:

```
→ http://192.168.1.42:5000
```

Share this URL with anyone on the same network — they can use it from phone or PC.

---

## 🛠 Available Tools

| Tool | Status | Notes |
|------|--------|-------|
| Merge PDF | ✅ Full | Combine multiple PDFs |
| Split PDF | ✅ Full | All pages, fixed, or custom ranges |
| Compress PDF | ✅ Full | Stream compression |
| Rotate PDF | ✅ Full | 90°, 180°, 270° |
| PDF to JPG | ✅ Full | Requires PyMuPDF |
| JPG to PDF | ✅ Full | Supports JPG, PNG, WEBP, BMP |
| Word to PDF | ⚠️ Needs LibreOffice | `sudo apt install libreoffice` |
| Excel to PDF | ⚠️ Needs LibreOffice | `sudo apt install libreoffice` |
| Protect PDF | ✅ Full | AES-128 encryption |
| Unlock PDF | ✅ Full | Removes password |
| Watermark PDF | ✅ Full | Text watermark, custom opacity |

---

## 📦 Python Dependencies

```
flask
flask-cors
pikepdf          # PDF manipulation (merge, split, rotate, protect, unlock)
Pillow           # Image processing
img2pdf          # Image → PDF
reportlab        # Watermark generation
PyMuPDF          # PDF → JPG (pymupdf package)
```

### Optional
```
libreoffice      # Word/Excel → PDF (install via apt/brew)
```

---

## 🌐 Network Access

The server binds to `0.0.0.0:5000` — accessible from any device on your LAN.

To restrict to localhost only, change `app.run(host='0.0.0.0', ...)` to `app.run(host='127.0.0.1', ...)` in `app.py`.

---

## 🔒 File Size Limit

Default: **100 MB** per upload. Change in `app.py`:

```python
app.config['MAX_CONTENT_LENGTH'] = 100 * 1024 * 1024  # 100MB
```

---

## 📁 Project Structure

```
ilovepdf-clone/
├── app.py          ← Flask backend with all PDF APIs
├── start.sh        ← One-click setup & run
├── README.md       ← This file
└── static/
    └── index.html  ← Full frontend (single file, no build needed)
```
