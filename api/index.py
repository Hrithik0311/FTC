from flask import Flask, request, jsonify
from flask_cors import CORS
import os
import requests
import base64
import json

app = Flask(__name__)
CORS(app)

# GitHub configuration
GITHUB_TOKEN = os.environ.get('GITHUB_TOKEN')
GITHUB_USER = 'Hrithik0311'
GITHUB_REPO = 'FTC'
GITHUB_BRANCH = 'main'

def get_file_sha(filepath):
    """Get the SHA of a file from GitHub (needed for updates)"""
    url = f"https://api.github.com/repos/{GITHUB_USER}/{GITHUB_REPO}/contents/{filepath}"
    headers = {
        'Authorization': f'token {GITHUB_TOKEN}',
        'Accept': 'application/vnd.github.v3+json'
    }
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        return response.json()['sha']
    return None

def update_github_file(filepath, content, message):
    """Update a file on GitHub"""
    url = f"https://api.github.com/repos/{GITHUB_USER}/{GITHUB_REPO}/contents/{filepath}"
    headers = {
        'Authorization': f'token {GITHUB_TOKEN}',
        'Accept': 'application/vnd.github.v3+json'
    }
    
    sha = get_file_sha(filepath)
    if not sha:
        return {'error': 'File not found'}, 404
    
    content_bytes = content.encode('utf-8')
    content_base64 = base64.b64encode(content_bytes).decode('utf-8')
    
    data = {
        'message': message,
        'content': content_base64,
        'sha': sha,
        'branch': GITHUB_BRANCH
    }
    
    response = requests.put(url, headers=headers, json=data)
    return response.json(), response.status_code

@app.route('/api/files', methods=['GET'])
def get_files():
    """Get all files from files.json"""
    url = f"https://raw.githubusercontent.com/{GITHUB_USER}/{GITHUB_REPO}/{GITHUB_BRANCH}/files.json"
    response = requests.get(url)
    if response.status_code == 200:
        return jsonify(response.json())
    return jsonify([]), 404

@app.route('/api/links', methods=['GET'])
def get_links():
    """Get all links from links.json"""
    url = f"https://raw.githubusercontent.com/{GITHUB_USER}/{GITHUB_REPO}/{GITHUB_BRANCH}/links.json"
    response = requests.get(url)
    if response.status_code == 200:
        return jsonify(response.json())
    return jsonify([]), 404

@app.route('/api/files', methods=['POST'])
def add_file():
    """Add a new file to files.json"""
    if not GITHUB_TOKEN:
        return jsonify({'error': 'GitHub token not configured'}), 500
    
    new_file = request.json
    
    # Get current files
    url = f"https://raw.githubusercontent.com/{GITHUB_USER}/{GITHUB_REPO}/{GITHUB_BRANCH}/files.json"
    response = requests.get(url)
    files = response.json() if response.status_code == 200 else []
    
    # Add new file
    files.append(new_file)
    
    # Update GitHub
    result, status = update_github_file(
        'files.json',
        json.dumps(files, indent=2),
        f'Add file: {new_file.get("name", "Untitled")}'
    )
    
    if status in [200, 201]:
        return jsonify({'success': True, 'file': new_file})
    return jsonify({'error': 'Failed to update GitHub'}), status

@app.route('/api/links', methods=['POST'])
def add_link():
    """Add a new link to links.json"""
    if not GITHUB_TOKEN:
        return jsonify({'error': 'GitHub token not configured'}), 500
    
    new_link = request.json
    
    # Get current links
    url = f"https://raw.githubusercontent.com/{GITHUB_USER}/{GITHUB_REPO}/{GITHUB_BRANCH}/links.json"
    response = requests.get(url)
    links = response.json() if response.status_code == 200 else []
    
    # Add new link
    links.append(new_link)
    
    # Update GitHub
    result, status = update_github_file(
        'links.json',
        json.dumps(links, indent=2),
        f'Add link: {new_link.get("name", "Untitled")}'
    )
    
    if status in [200, 201]:
        return jsonify({'success': True, 'link': new_link})
    return jsonify({'error': 'Failed to update GitHub'}), status

@app.route('/api/files/<int:index>', methods=['DELETE'])
def delete_file(index):
    """Delete a file from files.json"""
    if not GITHUB_TOKEN:
        return jsonify({'error': 'GitHub token not configured'}), 500
    
    # Get current files
    url = f"https://raw.githubusercontent.com/{GITHUB_USER}/{GITHUB_REPO}/{GITHUB_BRANCH}/files.json"
    response = requests.get(url)
    files = response.json() if response.status_code == 200 else []
    
    if index < 0 or index >= len(files):
        return jsonify({'error': 'Invalid index'}), 400
    
    deleted_file = files.pop(index)
    
    # Update GitHub
    result, status = update_github_file(
        'files.json',
        json.dumps(files, indent=2),
        f'Delete file: {deleted_file.get("name", "Untitled")}'
    )
    
    if status in [200, 201]:
        return jsonify({'success': True})
    return jsonify({'error': 'Failed to update GitHub'}), status

@app.route('/api/links/<int:index>', methods=['DELETE'])
def delete_link(index):
    """Delete a link from links.json"""
    if not GITHUB_TOKEN:
        return jsonify({'error': 'GitHub token not configured'}), 500
    
    # Get current links
    url = f"https://raw.githubusercontent.com/{GITHUB_USER}/{GITHUB_REPO}/{GITHUB_BRANCH}/links.json"
    response = requests.get(url)
    links = response.json() if response.status_code == 200 else []
    
    if index < 0 or index >= len(links):
        return jsonify({'error': 'Invalid index'}), 400
    
    deleted_link = links.pop(index)
    
    # Update GitHub
    result, status = update_github_file(
        'links.json',
        json.dumps(links, indent=2),
        f'Delete link: {deleted_link.get("name", "Untitled")}'
    )
    
    if status in [200, 201]:
        return jsonify({'success': True})
    return jsonify({'error': 'Failed to update GitHub'}), status

@app.route('/')
def home():
    return jsonify({'message': 'FTC Robotics API is running'})

# For Vercel
app = app
