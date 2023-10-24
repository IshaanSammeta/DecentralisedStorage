from flask import Flask, render_template, request, redirect, url_for, send_from_directory, session, flash
import os
import pandas as pd

app = Flask(__name__)
app.secret_key = 'your_secret_key'
app.config['UPLOAD_FOLDER'] = 'uploads'

# Route for user registration
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

# Route for the login page
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


# Route for the main page
@app.route('/')
def index():
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    files = os.listdir(app.config['UPLOAD_FOLDER'])
    return render_template('index.html', files=files)


# Route to handle file uploads
@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return redirect(request.url)
    file = request.files['file']
    if file.filename == '':
        return redirect(request.url)
    if file:
        filename = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
        file.save(filename)
        flash('File uploaded successfully', 'success')
        return redirect(url_for('index'))


# Route to handle file downloads
@app.route('/download/<filename>')
def download_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename, as_attachment=True)


# Route to log out
@app.route('/logout')
def logout():
    session.pop('logged_in', None)
    return redirect(url_for('login'))


if __name__ == '__main__':
    if not os.path.exists('users.xlsx'):
        initial_data = pd.DataFrame({'username': [], 'password': []})
        initial_data.to_excel('users.xlsx', index=False)

    app.run(debug=True)
