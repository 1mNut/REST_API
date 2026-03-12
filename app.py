from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
import mysql.connector
from mysql.connector import Error
from werkzeug.security import check_password_hash, generate_password_hash
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity, get_jwt

app = Flask(__name__)
CORS(app)

DB_CONFIG = {
    'host': 'localhost',
    'user': 'root',
    'password': '',
    'database': 'users'
}

def get_db_connection():
    try:
        connection = mysql.connector.connect(**DB_CONFIG)
        return connection
    except Error as e:
        print(f'Fel vid anslutning till MySQL: {e}')
        return None


@app.route('/', methods=['GET'])
def index():
    return '''<h1>Documentation</h1>
    <ul>
        <li>GET /users</li>
        <li>GET /users/&lt;id&gt;</li>
        <li>POST /users</li>
    </ul>'''

@app.route('/users', methods=['GET'])
def get_users():
    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)
    sql = "SELECT * FROM users"
    cursor.execute(sql)
    users = cursor.fetchall()
    if not users:
        return jsonify({'error': 'database error'}), 500
    return jsonify(users)

@app.route('/users/<int:user_id>', methods=['GET'])
def get_user(user_id):
    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)
    sql = "SELECT * FROM users WHERE id = %s"
    cursor.execute(sql, (user_id,))
    user = cursor.fetchone()
    if not user:
        return jsonify({'error': 'User not found'}), 404
    return jsonify(user)

@app.route('/users', methods=['POST'])
def create_user():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')
        
    connection = get_db_connection()
        
    cursor = connection.cursor()
    sql = "INSERT INTO users (username, password) VALUES (%s, %s)"
    cursor.execute(sql, (username, password))
        
    connection.commit()
    user_id = cursor.lastrowid
        
    user = {
    'id': user_id,
    'username': username,
    'password': password
    }
    return jsonify({'message': 'user created'}, user), 201

if __name__ == "__main__":
    app.run(debug=True, port=5500)