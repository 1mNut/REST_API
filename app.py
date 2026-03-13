from flask import Flask, request, jsonify
import mysql.connector
from mysql.connector import Error, IntegrityError
from werkzeug.security import check_password_hash, generate_password_hash
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity
from datetime import timedelta

app = Flask(__name__)
jwt = JWTManager(app)

app.config['JWT_SECRET_KEY'] = 'SUPER_SECRET_KEY'
app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(minutes=1)

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
        print(f'Error while connecting to MySQL: {e}')
        return None
    
def is_valid_user_data(data):
    return data and 'username' in data

@app.route('/', methods=['GET'])
def index():
    return '''<h1>Documentation</h1>
    <ul>
        <li>GET /users - Hämtar alla användare, kräver autentisering</li><br>
        <li>GET /users/&lt;id&gt; - Hämtar en specifik användare utifrån id, kräver autentisering</li><br>
        <li>POST /users - Skapar en ny användare som ska se ut som följande: {"username": "användarnamn", "password": "lösenord"}, kräver autentisering</li><br>
        <li>PUT /users/&lt;id&gt; - Uppdaterar en befintlig användare som ska se ut som följande: {"username": "användarnamn", "password": "lösenord"}, kräver autentisering</li><br>
        <li>POST /login - Loggar in en användare som ska se ut som följande: {"username": "användarnamn", "password": "lösenord"}</li><br>
        <li>GET /protected - visar vem som är inloggad, kräver autentisering</li><br>
        <li>GET /me - visar information om den inloggade användaren, kräver autentisering</li><br>
    </ul>'''

@app.route('/users', methods=['GET'])
@jwt_required()
def get_users():

    cursor = None
    connection = None

    try:
        connection = get_db_connection()
        if not connection:
            return jsonify({'error': 'database connection failed'}), 500
        cursor = connection.cursor(dictionary=True)
        sql = "SELECT * FROM users"
        cursor.execute(sql)
        users = cursor.fetchall()
        if not users:
            return jsonify({'error': 'database error'}), 500
        return jsonify(users)
    except Error:
        return jsonify({'error': 'something went wrong'}), 500
    finally:
        if cursor:
            cursor.close()
        if connection:
            connection.close()




@app.route('/users/<int:user_id>', methods=['GET'])
@jwt_required()
def get_user(user_id):

    cursor = None
    connection = None

    try:
        connection = get_db_connection()
        if not connection:
            return jsonify({'error': 'database connection failed'}), 500
        cursor = connection.cursor(dictionary=True)
        sql = "SELECT * FROM users WHERE id = %s"
        cursor.execute(sql, (user_id,))
        user = cursor.fetchone()
        if not user:
            return jsonify({'error': 'User not found'}), 404
        return jsonify(user)
    except Error:
        return jsonify({'error': 'something went wrong'}), 500
    finally:
        if cursor:
            cursor.close()
        if connection:
            connection.close()



@app.route('/users', methods=['POST'])
@jwt_required()
def create_user():

    cursor = None
    connection = None

    data = request.get_json(silent=True)
    if not data:
        return jsonify({'error': 'Incorrect Json format'}), 400

    username = data.get('username')
    password = data.get('password')

    if not username:
        return jsonify({'error': 'username required'}), 400
    if not password:
        return jsonify({'error': 'password required'}), 400

    try:
        connection = get_db_connection()
        if not connection:
            return jsonify({'error': 'database connection failed'}), 500
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
        return jsonify({'message': 'user created', 'user': user}), 201
    except IntegrityError:
        return jsonify({'error': 'username already exists'}), 400
    except Error:
        return jsonify({'error': 'something went wrong'}), 500
    finally:
        if cursor:
            cursor.close()
        if connection:
            connection.close()
    
@app.route('/users/<int:user_id>', methods=['PUT'])
@jwt_required()
def update_user(user_id):

    cursor = None
    connection = None

    data = request.get_json(silent=True)
    if not data:
        return jsonify({'error': 'Incorrect Json format'}), 400

    username = data.get('username')
    password = data.get('password')

    if not username:
        return jsonify({'error': 'username required'}), 400
    if not password:
        return jsonify({'error': 'password required'}), 400

    try:
        connection = get_db_connection()
        if not connection:
            return jsonify({'error': 'database connection failed'}), 500
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
    finally:
        if cursor:
            cursor.close()
        if connection:
            connection.close()

@app.route('/login', methods=['POST'])
def login():

    cursor = None
    connection = None

    data = request.get_json(silent=True)
    if not data:
        return jsonify({'error': 'Incorrect Json format'}), 400
    
    username = data.get('username')
    password = data.get('password')
   
    try:
        connection = get_db_connection()
        if not connection:
            return jsonify({'error': 'database connection failed'}), 500
        
        cursor = connection.cursor(dictionary=True)
        sql = "SELECT * FROM users WHERE username = %s"
        cursor.execute(sql, (username,))
        user = cursor.fetchone()

        if not user or not check_password_hash(user['password'], password):
            return jsonify({'error': 'Invalid username or password'}), 401
    
        if 'password' in user:
            del user['password']

        access_token = create_access_token(identity=username)

        return jsonify({"access_token": access_token,}), 200
    except Error:
        return jsonify({'error': 'database error'}), 500
    finally:
        if cursor:
            cursor.close()
        if connection:
            connection.close()



@app.route('/protected', methods=['GET'])
@jwt_required()
def protected():
    current_user = get_jwt_identity()
    return jsonify({'Logged in as': current_user}), 200

@app.route('/me', methods=['GET'])
@jwt_required()
def me():

    cursor = None
    connection = None

    current_user = get_jwt_identity()
    try:
        connection = get_db_connection()
        if not connection:
            return jsonify({'error': 'database connection failed'}), 500
        sql = "SELECT id, username FROM users WHERE username = %s"
        cursor = connection.cursor(dictionary=True)
        cursor.execute(sql, (current_user,))
        user = cursor.fetchone()
        if not user:
            return jsonify({'error': 'User not found'}), 404
        return jsonify(user), 200
    except Error:
        return jsonify({'error': 'database error'}), 500
    finally:
        if cursor:
            cursor.close()
        if connection:
            connection.close()

if __name__ == "__main__":
    app.run(debug=True, port=5000)