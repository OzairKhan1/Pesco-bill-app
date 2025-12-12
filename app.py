import os
import base64
import json
import zipfile
import io
import hashlib
from flask import Flask, render_template, request, jsonify, send_file
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = os.environ.get('SESSION_SECRET', 'dev-secret-key')

UPLOAD_FOLDER = 'uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)


def extract_images_from_txt(filepath):
    """Extract images from a .txt file and return image data with metadata."""
    extracted = []
    
    with open(filepath, 'rb') as f:
        content = f.read()
    
    try:
        text = content.decode('utf-8')
    except:
        text = content.decode('latin-1')
    
    if '\r\n' in text:
        line_ending = '\r\n'
        lines = text.split('\r\n')
    else:
        line_ending = '\n'
        lines = text.split('\n')
    
    if not lines:
        return [], None, line_ending
    
    header = lines[0]
    
    for i, line in enumerate(lines[1:], start=1):
        if not line.strip():
            continue
        
        try:
            parts = line.split(',', 3)
            if len(parts) < 4:
                continue
            
            record_subdiv = parts[0]
            year_month = parts[1]
            encrypted_meta = parts[2]
            original_base64 = parts[3]
            
            base64_data = original_base64
            if not base64_data.startswith('/9j/'):
                continue
            
            padding_needed = len(base64_data) % 4
            if padding_needed:
                base64_data += '=' * (4 - padding_needed)
            
            try:
                image_bytes = base64.b64decode(base64_data)
            except:
                continue
            
            image_hash = hashlib.md5(image_bytes).hexdigest()
            
            subdiv_nums = record_subdiv.replace('-', '')
            sequence = str(i).zfill(3)
            meter = "1"
            direction = "E"
            
            filename = f"{year_month}{subdiv_nums}{sequence}{meter}{direction}.jpg"
            
            extracted.append({
                'index': i,
                'filename': filename,
                'image_bytes': image_bytes,
                'image_hash': image_hash,
                'record_subdiv': record_subdiv,
                'year_month': year_month,
                'encrypted_meta': encrypted_meta,
                'original_base64': original_base64
            })
            
        except Exception as e:
            continue
    
    return extracted, header, line_ending


def create_zip_from_images(extracted_images, header, line_ending):
    """Create a ZIP file containing all extracted images and metadata."""
    zip_buffer = io.BytesIO()
    
    with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
        zip_file.writestr('header.txt', header)
        zip_file.writestr('line_ending.txt', 'CRLF' if line_ending == '\r\n' else 'LF')
        
        metadata = []
        for img in extracted_images:
            zip_file.writestr(f"images/{img['filename']}", img['image_bytes'])
            metadata.append({
                'index': img['index'],
                'filename': img['filename'],
                'image_hash': img['image_hash'],
                'record_subdiv': img['record_subdiv'],
                'year_month': img['year_month'],
                'encrypted_meta': img['encrypted_meta'],
                'original_base64': img['original_base64']
            })
        
        zip_file.writestr('metadata.json', json.dumps(metadata, indent=2))
    
    zip_buffer.seek(0)
    return zip_buffer


def encode_zip_to_txt(zip_file):
    """Convert a ZIP file back to the encoded .txt format."""
    with zipfile.ZipFile(zip_file, 'r') as zf:
        has_metadata = 'header.txt' in zf.namelist() and 'metadata.json' in zf.namelist()
        
        if has_metadata:
            header = zf.read('header.txt').decode('utf-8')
            metadata = json.loads(zf.read('metadata.json').decode('utf-8'))
            
            if 'line_ending.txt' in zf.namelist():
                le_type = zf.read('line_ending.txt').decode('utf-8').strip()
                line_ending = '\r\n' if le_type == 'CRLF' else '\n'
            else:
                line_ending = '\r\n'
        else:
            header = "Converted File"
            metadata = []
            line_ending = '\r\n'
        
        image_files = []
        for name in zf.namelist():
            lower_name = name.lower()
            if lower_name.endswith(('.jpg', '.jpeg', '.png')):
                image_files.append(name)
        
        image_files.sort()
        
        lines = [header]
        
        if has_metadata:
            for record in metadata:
                safe_filename = secure_filename(record['filename'])
                if not safe_filename:
                    continue
                
                possible_paths = [
                    f"images/{safe_filename}",
                    safe_filename,
                    f"images/{record['filename']}",
                    record['filename']
                ]
                
                image_path = None
                for path in possible_paths:
                    if path in zf.namelist():
                        image_path = path
                        break
                
                if not image_path:
                    continue
                
                image_bytes = zf.read(image_path)
                current_hash = hashlib.md5(image_bytes).hexdigest()
                
                if 'original_base64' in record and 'image_hash' in record:
                    if current_hash == record['image_hash']:
                        base64_data = record['original_base64']
                    else:
                        base64_data = base64.b64encode(image_bytes).decode('utf-8')
                else:
                    base64_data = base64.b64encode(image_bytes).decode('utf-8')
                
                line = f"{record['record_subdiv']},{record['year_month']},{record['encrypted_meta']},{base64_data}"
                lines.append(line)
        else:
            for idx, image_path in enumerate(image_files, start=1):
                filename = os.path.basename(image_path)
                parsed = parse_filename_for_metadata(filename)
                
                if parsed:
                    record_subdiv = parsed['record_subdiv']
                    year_month = parsed['year_month']
                    encrypted_meta = parsed['encrypted_meta']
                else:
                    record_subdiv = f"00-00-00{str(idx).zfill(4)}"
                    year_month = "202501"
                    encrypted_meta = "ENCODED"
                
                image_bytes = zf.read(image_path)
                base64_data = base64.b64encode(image_bytes).decode('utf-8')
                
                line = f"{record_subdiv},{year_month},{encrypted_meta},{base64_data}"
                lines.append(line)
        
        return line_ending.join(lines)


def parse_filename_for_metadata(filename):
    """Extract metadata from image filename following the naming convention."""
    basename = os.path.splitext(filename)[0]
    if len(basename) < 20:
        return None
    
    try:
        year_month = basename[:6]
        remaining = basename[6:]
        subdiv_code = remaining[:10] if len(remaining) >= 10 else remaining[:6]
        
        if len(subdiv_code) >= 6:
            formatted_subdiv = f"{subdiv_code[:2]}-{subdiv_code[2:4]}-{subdiv_code[4:6]}"
            if len(subdiv_code) > 6:
                formatted_subdiv += subdiv_code[6:]
        else:
            formatted_subdiv = subdiv_code
        
        return {
            'year_month': year_month,
            'record_subdiv': formatted_subdiv,
            'encrypted_meta': 'ENCODED'
        }
    except:
        return None


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/convert-txt-to-zip', methods=['POST'])
def convert_txt_to_zip():
    """Upload .txt file and download ZIP with extracted images."""
    if 'file' not in request.files:
        return jsonify({'error': 'No file uploaded'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400
    
    if not file.filename.lower().endswith('.txt'):
        return jsonify({'error': 'Please upload a .txt file'}), 400
    
    filename = secure_filename(file.filename)
    filepath = os.path.join(UPLOAD_FOLDER, filename)
    file.save(filepath)
    
    try:
        extracted, header, line_ending = extract_images_from_txt(filepath)
        
        if not extracted:
            os.remove(filepath)
            return jsonify({'error': 'No images found in the file'}), 400
        
        zip_buffer = create_zip_from_images(extracted, header, line_ending)
        
        zip_filename = filename.rsplit('.', 1)[0] + '_images.zip'
        
        os.remove(filepath)
        
        return send_file(
            zip_buffer,
            mimetype='application/zip',
            as_attachment=True,
            download_name=zip_filename
        )
        
    except Exception as e:
        if os.path.exists(filepath):
            os.remove(filepath)
        return jsonify({'error': f'Error processing file: {str(e)}'}), 500


@app.route('/convert-zip-to-txt', methods=['POST'])
def convert_zip_to_txt():
    """Upload ZIP file and download encoded .txt file."""
    if 'file' not in request.files:
        return jsonify({'error': 'No file uploaded'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400
    
    if not file.filename.lower().endswith('.zip'):
        return jsonify({'error': 'Please upload a .zip file'}), 400
    
    try:
        zip_buffer = io.BytesIO(file.read())
        
        with zipfile.ZipFile(zip_buffer, 'r') as zf:
            image_files = [f for f in zf.namelist() if f.lower().endswith(('.jpg', '.jpeg', '.png'))]
            if not image_files:
                return jsonify({'error': 'No image files found in the ZIP'}), 400
        
        zip_buffer.seek(0)
        txt_content = encode_zip_to_txt(zip_buffer)
        
        txt_filename = file.filename.rsplit('.', 1)[0].replace('_images', '') + '_encoded.txt'
        
        txt_buffer = io.BytesIO(txt_content.encode('utf-8'))
        
        return send_file(
            txt_buffer,
            mimetype='text/plain',
            as_attachment=True,
            download_name=txt_filename
        )
        
    except zipfile.BadZipFile:
        return jsonify({'error': 'Invalid or corrupted ZIP file'}), 400
    except Exception as e:
        return jsonify({'error': f'Error processing file: {str(e)}'}), 500


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
