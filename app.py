from flask import Flask, request, jsonify
from flask_cors import CORS
import mysql.connector
from mysql.connector import Error, IntegrityError
from werkzeug.security import check_password_hash, generate_password_hash
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity, get_jwt

app = Flask(__name__)
app.config['JWT_SECRET_KEY'] = 'SUPER_SECRET_KEY'

jwt = JWTManager(app)

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
    
def is_valid_user_data(data):
    return data and 'username' in data

@app.route('/', methods=['GET'])
def index():
    return '''<h1>Documentation</h1>
    <ul>
        <li>GET /users</li>
        <li>GET /users/&lt;id&gt;</li>
        <li>POST /users</li>
        <li>PUT /users/&lt;id&gt;</li>
    </ul>'''

@app.route('/users', methods=['GET'])
@jwt_required()
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
@jwt_required()
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
@jwt_required()
def create_user():
    data = request.get_json(silent=True)
    if not data:
        return jsonify({'error': 'Json format required'}), 400

    username = data.get('username')
    password = data.get('password')

    if not username:
        return jsonify({'error': 'username required'}), 400
    if not password:
        return jsonify({'error': 'password required'}), 400

    try:
        connection = get_db_connection()
        cursor = connection.cursor()
        hashed_password = generate_password_hash(password)
        sql = "INSERT INTO users (username, password) VALUES (%s, %s)"
        cursor.execute(sql, (username, hashed_password))
                
        connection.commit()
        user_id = cursor.lastrowid
                
        user = {
            'id': user_id,
            'username': username
        }
        return jsonify({'message': 'user created'}, user), 201
    except IntegrityError:
        return jsonify({'error': 'username already exists'}), 400
    except Error:
        return jsonify({'error': 'something went wrong'}), 500
    
@app.route('/users/<int:user_id>', methods=['PUT'])
@jwt_required()
def update_user(user_id):
    data = request.get_json(silent=True)
    if not data:
        return jsonify({'error': 'Json format required'}), 400

    username = data.get('username')
    password = data.get('password')

    if not username:
        jsonify({'error': 'username required'}), 400
    if not password:
        jsonify({'error': 'password required'}), 400

    try:
        connection = get_db_connection()
        cursor = connection.cursor()
        hashed_password = generate_password_hash(password)
        sql = """UPDATE users SET username = %s, password = %s WHERE id = %s"""
        cursor.execute(sql, (username, hashed_password, user_id))
        connection.commit()
        return jsonify({'message': 'user updated'})
    except IntegrityError:
        return jsonify({'error': 'username already exists'}), 400
    except Error:
        return jsonify({'error': 'something went wrong'}), 500

@app.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')
   
    connection = get_db_connection()
       
    cursor = connection.cursor(dictionary=True)
    sql = "SELECT * FROM users WHERE username = %s"
    cursor.execute(sql, (username,))
    user = cursor.fetchone()

    if not user or not check_password_hash(user['password'], password):
        return jsonify({'error': 'Invalid email or password'}), 401
    
    if 'password' in user:
        del user['password']

    access_token = create_access_token(identity=username)

    return jsonify(access_token=access_token), 200

# @app.route('/protected', methods=['GET'])
# @jwt_required()
# def protected():
#     current_user = get_jwt_identity()
#     print(get_jwt())
#     return jsonify(logged_in_as=current_user), 200



if __name__ == "__main__":
    app.run(debug=True, port=5000)