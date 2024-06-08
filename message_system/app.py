from flask import Flask, render_template, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import logging

# Set up basic logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///message_system.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False)
    role = db.Column(db.String(20), nullable=False)  # "dosen" atau "mahasiswa"
    messages_received = db.relationship('Message', backref='receiver', lazy=True, foreign_keys='Message.receiver_id')
    messages_sent = db.relationship('Message', backref='sender', lazy=True, foreign_keys='Message.sender_id')

class Message(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    sender_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    receiver_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    content = db.Column(db.String(200), nullable=False)
    timestamp = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        user_id = request.form['user_id']
        logger.debug(f"Login attempt with user_id: {user_id}")
        user = User.query.get(user_id)
        if user:
            logger.info(f"User {user_id} logged in successfully")
            return redirect(url_for('inbox', user_id=user.id))
        else:
            logger.error(f"User with user_id: {user_id} not found")
            return "User not found", 404
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form['name']
        role = request.form['role']
        logger.debug(f"Registering user with name: {name}, role: {role}")
        new_user = User(name=name, role=role)
        try:
            db.session.add(new_user)
            db.session.commit()
            logger.info(f"User {name} registered successfully")
        except Exception as e:
            logger.error(f"Error registering user: {e}")
            return "An error occurred while registering", 500
        return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/send_message', methods=['POST'])
def send_message():
    sender_id = request.form['sender_id']
    receiver_id = request.form['receiver_id']
    content = request.form['content']
    timestamp = datetime.now()
    
    logger.debug(f"Sending message from {sender_id} to {receiver_id} with content: {content}")
    message = Message(sender_id=sender_id, receiver_id=receiver_id, content=content, timestamp=timestamp)
    try:
        db.session.add(message)
        db.session.commit()
        logger.info(f"Message from {sender_id} to {receiver_id} sent successfully")
    except Exception as e:
        logger.error(f"Error sending message: {e}")
        return "An error occurred while sending the message", 500
    
    return redirect(url_for('inbox', user_id=sender_id))

@app.route('/inbox/<int:user_id>')
def inbox(user_id):
    user = User.query.get(user_id)
    if not user:
        logger.error(f"User with id: {user_id} not found")
        return "User not found", 404
    
    logger.debug(f"Fetching messages for user_id: {user_id}")
    received_messages = Message.query.filter_by(receiver_id=user.id).all()
    sent_messages = Message.query.filter_by(sender_id=user.id).all()
    
    return render_template('inbox.html', user=user, received_messages=received_messages, sent_messages=sent_messages)

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)
