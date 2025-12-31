from flask import Flask, request, jsonify
from flask_cors import CORS
import os, requests, base64, json, time

app = Flask(__name__)
CORS(app)

# CONFIGURATION
GITHUB_TOKEN = os.environ.get('GITHUB_TOKEN')
GITHUB_USER = 'Hrithik0311'
GITHUB_REPO = 'FTC'
GITHUB_BRANCH = 'main'
AUTHORIZED_USERS = os.environ.get('AUTHORIZED_USERS', '').split(',')

def get_github_file(path):
    url = f"https://api.github.com/repos/{GITHUB_USER}/{GITHUB_REPO}/contents/{path}"
    headers = {'Authorization': f'token {GITHUB_TOKEN}', 'Accept': 'application/vnd.github.v3+json'}
    response = requests.get(url, headers=headers)
    return response.json() if response.status_code == 200 else None

def update_github_file(path, content_obj, message):
    current_file = get_github_file(path)
    sha = current_file['sha'] if current_file else None
    
    url = f"https://api.github.com/repos/{GITHUB_USER}/{GITHUB_REPO}/contents/{path}"
    headers = {'Authorization': f'token {GITHUB_TOKEN}'}
    
    content_str = json.dumps(content_obj, indent=2)
    content_base64 = base64.b64encode(content_str.encode()).decode()
    
    data = {
        "message": message,
        "content": content_base64,
        "branch": GITHUB_BRANCH
    }
    if sha: data["sha"] = sha
    
    return requests.put(url, headers=headers, json=data)

@app.route('/api/auth/check', methods=['POST'])
def check_auth():
    user = request.json.get('username')
    if user in AUTHORIZED_USERS:
        return jsonify({'authorized': True, 'username': user})
    return jsonify({'authorized': False}), 403

@app.route('/api/files', methods=['GET', 'POST'])
def manage_files():
    if request.method == 'GET':
        # Bypass cache to get latest list
        r = requests.get(f"https://raw.githubusercontent.com/{GITHUB_USER}/{GITHUB_REPO}/{GITHUB_BRANCH}/files.json?cb={time.time()}")
        return jsonify(r.json() if r.status_code == 200 else [])
    
    # POST: Add new file metadata
    new_entry = request.json
    r = requests.get(f"https://raw.githubusercontent.com/{GITHUB_USER}/{GITHUB_REPO}/{GITHUB_BRANCH}/files.json")
    current_list = r.json() if r.status_code == 200 else []
    current_list.append(new_entry)
    update_github_file('files.json', current_list, f"Add file: {new_entry.get('name')}")
    return jsonify({'success': True})

@app.route('/api/files/upload', methods=['POST'])
def upload_blob():
    file = request.files['file']
    content = base64.b64encode(file.read()).decode()
    path = f"uploads/{file.filename}"
    
    url = f"https://api.github.com/repos/{GITHUB_USER}/{GITHUB_REPO}/contents/{path}"
    headers = {'Authorization': f'token {GITHUB_TOKEN}'}
    data = {"message": "Upload via Portal", "content": content, "branch": GITHUB_BRANCH}
    
    res = requests.put(url, headers=headers, json=data)
    return jsonify({'url': res.json()['content']['download_url'], 'filename': file.filename})

@app.route('/api/files/<int:index>', methods=['DELETE'])
def delete_file(index):
    r = requests.get(f"https://raw.githubusercontent.com/{GITHUB_USER}/{GITHUB_REPO}/{GITHUB_BRANCH}/files.json")
    current_list = r.json()
    if 0 <= index < len(current_list):
        current_list.pop(index)
        update_github_file('files.json', current_list, "Deleted file entry")
    return jsonify({'success': True})

# Minimal home route for testing
@app.route('/api')
def health():
    return jsonify({"status": "healthy", "repo": GITHUB_REPO})
