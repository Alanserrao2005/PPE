from flask import Flask, request, jsonify, render_template, session
from flask_mail import Mail, Message
from dotenv import load_dotenv
import random
import os

load_dotenv()

app = Flask(__name__, template_folder='templates')
app.secret_key = 'your_secret_key_here' # Change this in production

# Configure Flask-Mail
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = os.environ.get('MAIL_USERNAME', 'your_email@gmail.com')
app.config['MAIL_PASSWORD'] = os.environ.get('MAIL_PASSWORD', 'your_app_password')
app.config['MAIL_DEFAULT_SENDER'] = app.config['MAIL_USERNAME']

mail = Mail(app)

# In-memory store for OTPs (In a real app, use a database or Redis)
# Structure: { 'email@example.com': '123456' }
otps = {}

# Mock database
# Structure: {'email@example.com': {'name': 'Admin User', 'password': 'password123', 'role': 'Admin'}}
users_db = {
    'admin@example.com': {'name': 'Admin', 'password': 'admin123', 'role': 'Administrator'},
    'test@example.com': {'name': 'Test User', 'password': 'testpassword', 'role': 'Member'}
}

@app.route('/')
def index():
    return render_template('login.html')

@app.route('/login', methods=['POST'])
def login():
    data = request.json
    username = data.get('username')
    password = data.get('password')
    
    # Mock login logic checking against db
    user = users_db.get(username)
    # Also support old 'admin' username for backwards compatibility with UI default
    if username == 'admin' and password == 'admin123':
        session['user'] = {'name': 'Admin', 'role': 'Administrator'}
        return jsonify({'success': True, 'redirect': '/dashboard'})
        
    if user and user['password'] == password:
        session['user'] = {'name': user['name'], 'role': user['role']}
        return jsonify({'success': True, 'redirect': '/dashboard'})
        
    return jsonify({'success': False, 'message': 'Invalid credentials'}), 401

@app.route('/dashboard')
def dashboard():
    user = session.get('user', {'name': 'Admin', 'role': 'Administrator'})
    return render_template('dashboard.html', user=user)

@app.route('/api/send-otp', methods=['POST'])
def send_otp():
    data = request.json
    email = data.get('email')
    
    if not email:
        return jsonify({'success': False, 'message': 'Email is required'}), 400

    otp = str(random.randint(100000, 999999))
    otps[email] = otp
    
    try:
        msg = Message("Your PPE Detect AI Verification Code", recipients=[email])
        msg.body = f"Your verification code is: {otp}\n\nThis code will expire in 10 minutes."
        mail.send(msg)
        return jsonify({'success': True, 'message': 'OTP sent successfully'})
    except Exception as e:
        print(f"Failed to send email: {e}")
        return jsonify({'success': False, 'message': 'Failed to send OTP. Ensure your email credentials are set.'}), 500

@app.route('/api/verify-otp', methods=['POST'])
def verify_otp():
    data = request.json
    email = data.get('email')
    user_otp = data.get('otp')
    
    if not email or not user_otp:
        return jsonify({'success': False, 'message': 'Email and OTP are required'}), 400
        
    valid_otp = otps.get(email)
    
    if valid_otp and valid_otp == user_otp:
        # OTP is correct
        otps.pop(email, None) # Clear OTP after successful verification
        return jsonify({'success': True, 'message': 'Email verified successfully'})
    else:
        return jsonify({'success': False, 'message': 'Invalid OTP'}), 400

@app.route('/api/signup', methods=['POST'])
def signup():
    data = request.json
    email = data.get('email')
    password = data.get('password')
    name = data.get('name')
    
    if email in users_db:
         return jsonify({'success': False, 'message': 'User already exists.'}), 400
         
    users_db[email] = {'name': name, 'password': password, 'role': 'Member'}
    return jsonify({'success': True, 'message': 'Account created successfully'})

@app.route('/api/reset-password', methods=['POST'])
def reset_password():
    data = request.json
    email = data.get('email')
    new_password = data.get('password')
    
    user = users_db.get(email)
    
    if user:
        if user['password'] == new_password:
            return jsonify({'success': False, 'message': 'You cannot use your old password.'}), 400
        user['password'] = new_password
        return jsonify({'success': True, 'message': 'Password reset successfully'})
    else:
        # Mock logic to still let you reset a non-existent email if it's not the generic 'admin123'
        if new_password == 'admin123':
             return jsonify({'success': False, 'message': 'You cannot use your old password.'}), 400
             
        users_db[email] = {'name': 'New User', 'password': new_password, 'role': 'Member'}
        return jsonify({'success': True, 'message': 'Password reset successfully'})

if __name__ == '__main__':
    app.run(debug=True, port=5000)
