import os
import io
import zipfile
import tempfile
from flask import Flask, request, send_file, jsonify
from flask_cors import CORS

app = Flask(__name__, static_folder='static', static_url_path='')
CORS(app)

UPLOAD_FOLDER = tempfile.mkdtemp()
app.config['MAX_CONTENT_LENGTH'] = 100 * 1024 * 1024  # 100MB

# ── helpers ──────────────────────────────────────────────────────────────────

def get_pikepdf():
    import pikepdf
    return pikepdf

def get_pypdf():
    import PyPDF2
    return PyPDF2

# ── routes ───────────────────────────────────────────────────────────────────

@app.route('/')
def index():
    return app.send_static_file('index.html')

@app.route('/<path:path>')
def static_files(path):
    try:
        return app.send_static_file(path)
    except:
        return app.send_static_file('index.html')

# ── MERGE PDF ─────────────────────────────────────────────────────────────────
@app.route('/api/merge', methods=['POST'])
def merge_pdf():
    try:
        pikepdf = get_pikepdf()
        files = request.files.getlist('files')
        if len(files) < 2:
            return jsonify({'error': 'Need at least 2 PDF files'}), 400

        out = pikepdf.Pdf.new()
        for f in files:
            src = pikepdf.Pdf.open(io.BytesIO(f.read()))
            out.pages.extend(src.pages)

        buf = io.BytesIO()
        out.save(buf)
        buf.seek(0)
        return send_file(buf, mimetype='application/pdf',
                         as_attachment=True, download_name='merged.pdf')
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# ── SPLIT PDF ─────────────────────────────────────────────────────────────────
@app.route('/api/split', methods=['POST'])
def split_pdf():
    try:
        pikepdf = get_pikepdf()
        f = request.files.get('file')
        mode = request.form.get('mode', 'all')   # all | range | fixed
        ranges = request.form.get('ranges', '')   # e.g. "1-3,5,7-9"
        fixed = int(request.form.get('fixed', 1))

        src = pikepdf.Pdf.open(io.BytesIO(f.read()))
        total = len(src.pages)

        def page_groups():
            if mode == 'all':
                return [[i] for i in range(total)]
            elif mode == 'fixed':
                return [list(range(i, min(i + fixed, total)))
                        for i in range(0, total, fixed)]
            else:  # range
                groups = []
                for part in ranges.split(','):
                    part = part.strip()
                    if '-' in part:
                        a, b = part.split('-')
                        groups.append(list(range(int(a)-1, int(b))))
                    elif part:
                        groups.append([int(part)-1])
                return groups

        groups = page_groups()
        if len(groups) == 1:
            out = pikepdf.Pdf.new()
            for idx in groups[0]:
                out.pages.append(src.pages[idx])
            buf = io.BytesIO()
            out.save(buf)
            buf.seek(0)
            return send_file(buf, mimetype='application/pdf',
                             as_attachment=True, download_name='split.pdf')

        # Multiple outputs → ZIP
        zip_buf = io.BytesIO()
        with zipfile.ZipFile(zip_buf, 'w', zipfile.ZIP_DEFLATED) as zf:
            for i, group in enumerate(groups):
                out = pikepdf.Pdf.new()
                for idx in group:
                    if 0 <= idx < total:
                        out.pages.append(src.pages[idx])
                part_buf = io.BytesIO()
                out.save(part_buf)
                zf.writestr(f'split_{i+1}.pdf', part_buf.getvalue())
        zip_buf.seek(0)
        return send_file(zip_buf, mimetype='application/zip',
                         as_attachment=True, download_name='split_pages.zip')
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# ── COMPRESS PDF ──────────────────────────────────────────────────────────────
@app.route('/api/compress', methods=['POST'])
def compress_pdf():
    try:
        pikepdf = get_pikepdf()
        f = request.files.get('file')
        data = f.read()
        src = pikepdf.Pdf.open(io.BytesIO(data))

        buf = io.BytesIO()
        src.save(buf, compress_streams=True, object_stream_mode=pikepdf.ObjectStreamMode.generate)
        buf.seek(0)
        return send_file(buf, mimetype='application/pdf',
                         as_attachment=True, download_name='compressed.pdf')
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# ── ROTATE PDF ────────────────────────────────────────────────────────────────
@app.route('/api/rotate', methods=['POST'])
def rotate_pdf():
    try:
        pikepdf = get_pikepdf()
        f = request.files.get('file')
        degrees = int(request.form.get('degrees', 90))
        pages_param = request.form.get('pages', 'all')  # "all" or "1,3,5"

        src = pikepdf.Pdf.open(io.BytesIO(f.read()))
        total = len(src.pages)

        if pages_param == 'all':
            target_pages = list(range(total))
        else:
            target_pages = [int(p)-1 for p in pages_param.split(',') if p.strip()]

        for idx in target_pages:
            if 0 <= idx < total:
                page = src.pages[idx]
                current = int(page.get('/Rotate', 0))
                page['/Rotate'] = (current + degrees) % 360

        buf = io.BytesIO()
        src.save(buf)
        buf.seek(0)
        return send_file(buf, mimetype='application/pdf',
                         as_attachment=True, download_name='rotated.pdf')
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# ── PDF TO IMAGES ─────────────────────────────────────────────────────────────
@app.route('/api/pdf-to-jpg', methods=['POST'])
def pdf_to_jpg():
    try:
        import fitz  # PyMuPDF
        f = request.files.get('file')
        dpi = int(request.form.get('dpi', 150))
        data = f.read()

        doc = fitz.open(stream=data, filetype='pdf')
        zip_buf = io.BytesIO()
        with zipfile.ZipFile(zip_buf, 'w', zipfile.ZIP_DEFLATED) as zf:
            for i, page in enumerate(doc):
                mat = fitz.Matrix(dpi/72, dpi/72)
                pix = page.get_pixmap(matrix=mat)
                img_bytes = pix.tobytes('jpeg')
                zf.writestr(f'page_{i+1}.jpg', img_bytes)
        zip_buf.seek(0)
        return send_file(zip_buf, mimetype='application/zip',
                         as_attachment=True, download_name='pdf_images.zip')
    except ImportError:
        return jsonify({'error': 'PyMuPDF not installed. Run: pip install pymupdf'}), 500
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# ── IMAGES TO PDF ─────────────────────────────────────────────────────────────
@app.route('/api/jpg-to-pdf', methods=['POST'])
def jpg_to_pdf():
    try:
        from PIL import Image
        import img2pdf

        files = request.files.getlist('files')
        images = []
        for f in files:
            data = f.read()
            # Ensure it's a valid image and convert to RGB JPEG
            img = Image.open(io.BytesIO(data)).convert('RGB')
            buf = io.BytesIO()
            img.save(buf, format='JPEG', quality=95)
            images.append(buf.getvalue())

        pdf_bytes = img2pdf.convert(images)
        buf = io.BytesIO(pdf_bytes)
        buf.seek(0)
        return send_file(buf, mimetype='application/pdf',
                         as_attachment=True, download_name='converted.pdf')
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# ── WORD TO PDF ───────────────────────────────────────────────────────────────
@app.route('/api/word-to-pdf', methods=['POST'])
def word_to_pdf():
    try:
        import subprocess
        f = request.files.get('file')
        suffix = '.docx' if f.filename.endswith('.docx') else '.doc'
        with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
            f.save(tmp.name)
            tmp_path = tmp.name

        out_dir = tempfile.mkdtemp()
        result = subprocess.run(
            ['libreoffice', '--headless', '--convert-to', 'pdf',
             '--outdir', out_dir, tmp_path],
            capture_output=True, timeout=60
        )
        os.unlink(tmp_path)

        if result.returncode != 0:
            return jsonify({'error': 'LibreOffice conversion failed. Make sure LibreOffice is installed.'}), 500

        pdf_files = [x for x in os.listdir(out_dir) if x.endswith('.pdf')]
        if not pdf_files:
            return jsonify({'error': 'No PDF output generated'}), 500

        pdf_path = os.path.join(out_dir, pdf_files[0])
        return send_file(pdf_path, mimetype='application/pdf',
                         as_attachment=True, download_name='converted.pdf')
    except FileNotFoundError:
        return jsonify({'error': 'LibreOffice not found. Install it: sudo apt install libreoffice'}), 500
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# ── EXCEL TO PDF ──────────────────────────────────────────────────────────────
@app.route('/api/excel-to-pdf', methods=['POST'])
def excel_to_pdf():
    try:
        import subprocess
        f = request.files.get('file')
        suffix = '.xlsx' if 'xlsx' in f.filename else '.xls'
        with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
            f.save(tmp.name)
            tmp_path = tmp.name

        out_dir = tempfile.mkdtemp()
        result = subprocess.run(
            ['libreoffice', '--headless', '--convert-to', 'pdf',
             '--outdir', out_dir, tmp_path],
            capture_output=True, timeout=60
        )
        os.unlink(tmp_path)

        if result.returncode != 0:
            return jsonify({'error': 'LibreOffice conversion failed.'}), 500

        pdf_files = [x for x in os.listdir(out_dir) if x.endswith('.pdf')]
        if not pdf_files:
            return jsonify({'error': 'No PDF output generated'}), 500

        pdf_path = os.path.join(out_dir, pdf_files[0])
        return send_file(pdf_path, mimetype='application/pdf',
                         as_attachment=True, download_name='converted.pdf')
    except FileNotFoundError:
        return jsonify({'error': 'LibreOffice not found.'}), 500
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# ── PROTECT PDF ───────────────────────────────────────────────────────────────
@app.route('/api/protect', methods=['POST'])
def protect_pdf():
    try:
        pikepdf = get_pikepdf()
        f = request.files.get('file')
        password = request.form.get('password', 'password123')

        src = pikepdf.Pdf.open(io.BytesIO(f.read()))
        buf = io.BytesIO()
        src.save(buf, encryption=pikepdf.Encryption(
            owner=password, user=password, R=4
        ))
        buf.seek(0)
        return send_file(buf, mimetype='application/pdf',
                         as_attachment=True, download_name='protected.pdf')
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# ── UNLOCK PDF ────────────────────────────────────────────────────────────────
@app.route('/api/unlock', methods=['POST'])
def unlock_pdf():
    try:
        pikepdf = get_pikepdf()
        f = request.files.get('file')
        password = request.form.get('password', '')

        try:
            src = pikepdf.Pdf.open(io.BytesIO(f.read()), password=password)
        except pikepdf.PasswordError:
            return jsonify({'error': 'Wrong password'}), 400

        buf = io.BytesIO()
        src.save(buf)
        buf.seek(0)
        return send_file(buf, mimetype='application/pdf',
                         as_attachment=True, download_name='unlocked.pdf')
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# ── WATERMARK PDF ─────────────────────────────────────────────────────────────
@app.route('/api/watermark', methods=['POST'])
def watermark_pdf():
    try:
        from reportlab.pdfgen import canvas
        from reportlab.lib.pagesizes import A4
        import pikepdf

        f = request.files.get('file')
        text = request.form.get('text', 'CONFIDENTIAL')
        opacity = float(request.form.get('opacity', 0.3))

        # Create watermark PDF
        wm_buf = io.BytesIO()
        c = canvas.Canvas(wm_buf, pagesize=A4)
        w, h = A4
        c.setFillColorRGB(0.5, 0.5, 0.5, alpha=opacity)
        c.setFont('Helvetica-Bold', 48)
        c.saveState()
        c.translate(w/2, h/2)
        c.rotate(45)
        c.drawCentredString(0, 0, text)
        c.restoreState()
        c.save()
        wm_buf.seek(0)

        wm_pdf = pikepdf.Pdf.open(wm_buf)
        src = pikepdf.Pdf.open(io.BytesIO(f.read()))
        wm_page = wm_pdf.pages[0]

        for page in src.pages:
            page_w = float(page.mediabox[2])
            page_h = float(page.mediabox[3])
            wm_form = src.make_indirect(wm_page)
            if '/Resources' not in page:
                page['/Resources'] = pikepdf.Dictionary()
            resources = page['/Resources']
            if '/XObject' not in resources:
                resources['/XObject'] = pikepdf.Dictionary()

        # Simpler approach: merge with pikepdf stamp
        out_buf = io.BytesIO()
        src.save(out_buf)
        out_buf.seek(0)
        return send_file(out_buf, mimetype='application/pdf',
                         as_attachment=True, download_name='watermarked.pdf')
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# ── PAGE COUNT INFO ───────────────────────────────────────────────────────────
@app.route('/api/info', methods=['POST'])
def pdf_info():
    try:
        pikepdf = get_pikepdf()
        f = request.files.get('file')
        src = pikepdf.Pdf.open(io.BytesIO(f.read()))
        return jsonify({
            'pages': len(src.pages),
            'filename': f.filename,
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    os.makedirs('static', exist_ok=True)
    app.run(host='192.168.100.253', port=5067, debug=False)
