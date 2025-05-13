from flask import Flask, render_template, request, redirect, url_for, Response, send_from_directory
import os
import time
from flask_cors import CORS

app = Flask(__name__)
CORS(app)  # Enable CORS
UPLOAD_FOLDER = 'current.csv'

# Serve static files (CSS/JS)
@app.route('/static/<path:filename>')
def static_files(filename):
    return send_from_directory('static', filename)

@app.route('/')
def upload_page():
    return render_template('File_receiving.html')

@app.route('/files', methods=['POST'])
def upload_file():
    if 'get_csv' not in request.files:
        return "No file part", 400
    file = request.files['get_csv']
    if file.filename == '':
        return "No selected file", 400
    file.save(UPLOAD_FOLDER)
    return redirect(url_for('graph_page'))

@app.route('/graph')
def graph_page():
    return render_template('index.html')

@app.route('/data.csv')
def serve_csv():
    # Always open fresh file handle
    with open(UPLOAD_FOLDER, 'r') as f:
        content = f.read()
    
    response = Response(content, mimetype='text/csv')
    # Prevent caching
    response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '0'
    return response

@app.route('/check-update')
def check_update():
    try:
        # Force fresh stat every time
        stat = os.stat(UPLOAD_FOLDER)
        return {
            'last_modified': stat.st_mtime,
            'file_size': stat.st_size  # Also check size changes
        }
    except FileNotFoundError:
        return {'error': 'File not found'}, 404

def read_file_fresh():
    """Reads file with retries and Windows-safe operations"""
    file_path = os.path.abspath(UPLOAD_FOLDER)
    for _ in range(5):  # Retry up to 5 times
        try:
            with open(file_path, 'rb') as f:  # Note: binary mode
                # Go to end, get position (size)
                f.seek(0, os.SEEK_END)
                size = f.tell()
                f.seek(0)  # Rewind
                content = f.read().decode('utf-8')  # Read all and decode
                return content
        except (IOError, PermissionError) as e:
            print(f"Read failed (attempt {_+1}): {str(e)}")
            time.sleep(0.1)
    if os.name == 'nt':  # Windows only
        try:
            os.close(os.open(UPLOAD_FOLDER, os.O_RDONLY | os.O_EXCL))
        except:
            pass
    return ""  # Return empty if all retries fail
def read_file_via_copy():
    import shutil
    temp_file = f"{UPLOAD_FOLDER}.tmp"
    try:
        shutil.copy2(UPLOAD_FOLDER, temp_file)
        with open(temp_file, 'r') as f:
            return f.read()
    finally:
        try:
            os.remove(temp_file)
        except:
            pass

##################################### DEBUG ########################################
def get_csv_content():
    """Always returns fresh file content"""
    for _ in range(3):  # Retry 3 times if file is locked
        try:
            with open(UPLOAD_FOLDER, 'r') as f:
                return f.read()
        except IOError:
            time.sleep(0.1)
    return ""  # Return empty if can't read


@app.route('/force-refresh')
def force_refresh():
    content = read_file_fresh()
    print(f"Read {len(content)} bytes from {os.path.abspath(UPLOAD_FOLDER)}")
    return Response(content, mimetype='text/plain')

@app.route('/debug/file-info')
def debug_file_info():
    stat = os.stat(UPLOAD_FOLDER)
    return {
        'path': os.path.abspath(UPLOAD_FOLDER),
        'size': stat.st_size,
        'modified': stat.st_mtime,
        'current_time': time.time(),
        'content_sample': get_csv_content()[:200]  # First 200 chars
    }

@app.route('/debug/csv-content')
def debug_csv_content():
    if not os.path.exists(UPLOAD_FOLDER):
        return "File doesn't exist", 404
        
    with open(UPLOAD_FOLDER, 'r') as f:
        content = f.read()
        
    return Response(
        f"File exists. Length: {len(content)} bytes\n\n{content}",
        mimetype='text/plain'
    )

@app.route('/test-append')
def test_append():
    test_data = f"\nTest data at {time.time()}\n"
    try:
        with open(UPLOAD_FOLDER, 'a') as f:
            f.write(test_data)
            f.flush()  # Force write to disk
            os.fsync(f.fileno())  # Ensure OS-level write
        return f"Appended: {test_data}"
    except Exception as e:
        return f"Append failed: {str(e)}", 500

@app.route('/cross-verify')
def cross_verify():
    # Get what Flask sees
    flask_content = read_file_fresh()
    
    # Direct OS read for comparison
    try:
        with open(UPLOAD_FOLDER, 'rb') as f:
            os_content = f.read().decode('utf-8')
    except Exception as e:
        os_content = f"OS read failed: {str(e)}"
    
    return {
        'flask_read_length': len(flask_content),
        'os_read_length': len(os_content),
        'match': flask_content == os_content,
        'file_info': {
            'path': os.path.abspath(UPLOAD_FOLDER),
            'size': os.path.getsize(UPLOAD_FOLDER),
            'modified': os.path.getmtime(UPLOAD_FOLDER)
        }
    }

if __name__ == '__main__':
    app.run(debug=True, port=5000)