from flask import Flask, render_template, request, redirect, url_for, session, flash, Response, g
import sqlite3
import os
import requests

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your_secret_key'
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['DATABASE'] = 'users.db'  # SQLite database file

# Function to initialize the database
def init_db():
    with app.app_context():
        db = get_db()
        cursor = db.cursor()
        cursor.execute('''  
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL,
                password TEXT NOT NULL
            )
        ''')
        cursor.execute('''
                    CREATE TABLE IF NOT EXISTS user_files (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        user_id INTEGER,
                        ipfs_hash TEXT NOT NULL,
                        FOREIGN KEY (user_id) REFERENCES users (id)
                    )
                ''')
        db.commit()

# Function to get a database connection
def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(app.config['DATABASE'])
    return db

# Function to query the database
def query_db(query, args=(), one=False):
    cur = get_db().execute(query, args)
    rv = cur.fetchall()
    cur.close()
    return (rv[0] if rv else None) if one else rv

# Initialize the database
init_db()

# Replace with the IP address and port of your IPFS node
ipfs_api_url = "http://localhost:5001/api/v0"

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
        return None

# Function to save user-file association in the database
def save_user_file(user_id, ipfs_hash):
    db = get_db()
    db.execute('INSERT INTO user_files (user_id, ipfs_hash) VALUES (?, ?)', [user_id, ipfs_hash])
    db.commit()

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
# Modify this function in your app.py
def get_user_ipfs_hashes(user_id):
    results = query_db('SELECT ipfs_hash FROM user_files WHERE user_id = ?', [user_id])
    return [result[0] for result in results]

@app.route('/')
def welcome():
    return render_template('welcome.html')


@app.route('/index')
def index():
    if not session.get('logged_in'):
        flash('Please log in first.', 'error')
        return redirect(url_for('login'))

    user_id = session['user_id']
    user_ipfs_hashes = get_user_ipfs_hashes(user_id)

    return render_template('index.html', files=user_ipfs_hashes)


@app.route('/upload', methods=['POST'])
def upload():
    if not session.get('logged_in'):
        flash('Please log in first.', 'error')
        return redirect(url_for('login'))

    if 'file' not in request.files:
        flash('No file part', 'error')
        return redirect(url_for('index'))

    file = request.files['file']
    if file.filename == '':
        flash('No selected file', 'error')
        return redirect(url_for('index'))

    file_content = file.read()
    ipfs_hash = upload_to_ipfs(file_content)

    if ipfs_hash:
        user_id = session['user_id']
        save_user_file(user_id, ipfs_hash)
        flash('File uploaded to IPFS successfully', 'success')
    else:
        flash('Failed to upload the file to IPFS', 'error')

    return redirect(url_for('index'))


@app.route('/download/<filename>')
def download_file(filename):
    if not session.get('logged_in'):
        flash('Please log in first.', 'error')
        return redirect(url_for('login'))

    user_id = session['user_id']
    user_ipfs_hashes = get_user_ipfs_hashes(user_id)

    if filename not in user_ipfs_hashes:
        flash('You do not have permission to download this file.', 'error')
        return redirect(url_for('index'))

    ipfs_hash = filename
    downloaded_content = download_from_ipfs(ipfs_hash)

    if downloaded_content:
        response = Response(downloaded_content, content_type='application/octet-stream')
        response.headers['Content-Disposition'] = f'attachment; filename={ipfs_hash}.txt'
        return response
    else:
        flash('Failed to download the file from IPFS', 'error')
        return redirect(url_for('index'))


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        user = query_db('SELECT * FROM users WHERE username = ?', [username], one=True)
        if user:
            flash('Username already exists. Please choose another one.', 'error')
        else:
            db = get_db()
            db.execute('INSERT INTO users (username, password) VALUES (?, ?)', [username, password])
            db.commit()
            flash('Your account has been created! You can now log in.', 'success')
            return redirect(url_for('login'))
    return render_template('register.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        user = query_db('SELECT * FROM users WHERE username = ? AND password = ?', [username, password], one=True)

        if user:
            user_id = user[0]  # Assuming user_id is the first column in the SELECT statement
            session['logged_in'] = True
            session['user_id'] = user_id  # Set the user ID in the session
            flash('Login successful', 'success')
            return redirect(url_for('index'))
        else:
            flash('Login failed. Please try again.', 'error')
    return render_template('login.html')


@app.route('/logout')
def logout():
    if session.get('logged_in'):
        session.pop('logged_in', None)
        session.pop('user_id', None)
        flash('Logout successful', 'success')
    return redirect(url_for('login'))


if __name__ == '__main__':
    app.run(debug=True)
