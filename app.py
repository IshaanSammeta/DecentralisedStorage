from flask import Flask, render_template, request, redirect, url_for, session, flash, Response
import os
import pandas as pd
import requests

# Replace with the IP address and port of your IPFS node
ipfs_api_url = "http://192.168.29.3:5001/api/v0"

app = Flask(__name__)
app.secret_key = 'your_secret_key'
app.config['UPLOAD_FOLDER'] = 'uploads'

# Dictionary to store uploaded file information (IPFS hashes)
uploaded_files = {}


# Function to upload a file to IPFS
def upload_to_ipfs(file_content):
    files = {'file': ('filename.txt', file_content)}
    response = requests.post(f"{ipfs_api_url}/add", files=files)

    if response.status_code == 200:
        ipfs_hash = response.json()['Hash']
        return ipfs_hash
    else:
        return Nonegit


# Function to download a file from IPFS
def download_from_ipfs(ipfs_hash):
    print(f"Fetching IPFS content from: {ipfs_api_url}/cat/{ipfs_hash}")
    response = requests.get(f"{ipfs_api_url}/cat/{ipfs_hash}")
    if response.status_code == 200:
        file_content = response.content
        return file_content
    else:
        return None


# Actual data retrieval logic to get IPFS hashes
def get_ipfs_hashes():
    return list(uploaded_files.keys())


@app.route('/')
def index():
    if not session.get('logged_in'):
        return redirect(url_for('login'))

    ipfs_hashes = get_ipfs_hashes()

    return render_template('index.html', files=ipfs_hashes)


@app.route('/upload', methods=['POST'])
def upload():
    if not session.get('logged_in'):
        return redirect(url_for('login'))

    if 'file' not in request.files:
        flash('No file part', 'error')
        return redirect(request.url)

    file = request.files['file']
    if file.filename == '':
        flash('No selected file', 'error')
        return redirect(request.url)

    if file:
        file_content = file.read()
        ipfs_hash = upload_to_ipfs(file_content)

        if ipfs_hash:
            uploaded_files[ipfs_hash] = file.filename
            flash('File uploaded to IPFS successfully', 'success')
            return redirect(url_for('index'))
        else:
            flash('Failed to upload the file to IPFS', 'error')
            return redirect(request.url)


@app.route('/download/<filename>')
def download_file(filename):
    if not session.get('logged_in'):
        return redirect(url_for('login'))

    ipfs_hash = filename
    downloaded_content = download_from_ipfs(ipfs_hash)
    # print(f"IPFS Hash (filename): {filename}")
    # print("Uploaded Files:", uploaded_files)
    print(downloaded_content)
    if downloaded_content:
        response = Response(downloaded_content, content_type='application/octet-stream')
        response.headers['Content-Disposition'] = f'attachment; filename={uploaded_files[ipfs_hash]}.txt'
        return response
    else:
        flash('Failed to download the file from IPFS', 'error')
        return redirect(url_for('index'))


@app.route('/download/QmbaS16zkJtjPhtkPTJrMrWm7T5fBKbyMRVhcraedF9BzL')
def test():
    downloaded_content='QmbaS16zkJtjPhtkPTJrMrWm7T5fBKbyMRVhcraedF9BzL'
    response = Response(downloaded_content, content_type='application/octet-stream')
    response.headers['Content-Disposition'] = f'attachment; filename={uploaded_files[downloaded_content]}.txt'
    return response

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        user_data = pd.read_excel('users.xlsx')
        if username in user_data['username'].tolist():
            flash('Username already exists. Please choose another one.', 'error')
        else:
            new_user = pd.DataFrame({'username': [username], 'password': [password]})
            user_data = pd.concat([user_data, new_user], ignore_index=True)
            user_data.to_excel('users.xlsx', index=False)
            flash('Your account has been created! You can now log in.', 'success')
            return redirect(url_for('login'))
    return render_template('register.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        user_data = pd.read_excel('users.xlsx')
        user = user_data[user_data['username'] == username]

        if user.empty or user['password'].values[0] != password:
            flash('Login failed. Please try again.', 'error')
        else:
            session['logged_in'] = True
            flash('Login successful', 'success')
            return redirect(url_for('index'))
    return render_template('login.html')


@app.route('/logout')
def logout():
    session.pop('logged_in', None)
    return redirect(url_for('login'))


if __name__ == '__main__':
    app.run(debug=True)
