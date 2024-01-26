from flask import Flask, request, jsonify
from flask_jwt_extended import JWTManager
from datetime import timedelta
from flask_jwt_extended import create_access_token
from flask_jwt_extended import jwt_required, get_jwt_identity
from azure.storage.blob import BlockBlobService
import pyodbc, struct ,os
import json

db = os.environ["AZURE_SQL_DB"]
dbname = os.environ["AZURE_SQL_DBNAME"]
logindb = os.environ["AZURE_SQL_LOGINDB"]
passworddb = os.environ["AZURE_SQL_PASSWORDDB"]
ACCESS_EXPIRES = timedelta(hours=1)


connection_string = "Driver={ODBC Driver 18 for SQL Server};Server=tcp:"+db+".database.windows.net,1433;Database="+dbname+";Uid="+logindb+";Pwd="+passworddb+";Encrypt=yes;TrustServerCertificate=no;Connection Timeout=30;"
app = Flask(__name__)

app.config["JWT_SECRET_KEY"] = os.environ["APP_SUPER_KEY"] 
app.config["JWT_ACCESS_TOKEN_EXPIRES"] = ACCESS_EXPIRES
jwt = JWTManager(app)

@app.route("/")
def index():
    return "<h1>Hello Azure!</h1>"

@app.route("/login", methods=["POST"])
def create_token():
    name = request.json.get("pseudo", None)
    password = request.json.get("password", None)

    records=[]
    try:
        conn = get_conn()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users where pseudo='"+name+"' and mdp='"+password+"';")
        records = cursor.fetchall()
    except Exception as e:
        print(e)

    if len(records)!=1:
        # The user was not found on the database
        return jsonify({"msg": "Bad username or password"}), 401
    
    # Create a new token with the user id inside
    access_token = create_access_token(identity=name)
    return jsonify({ "token": access_token, "user_id": name })

@app.route('/user', methods=['GET'])
@jwt_required()
def get_user():
    name = request.args.get('pseudo')
    records=[]
    try:
        conn = get_conn()
        cursor = conn.cursor()

        if name == None :
            cursor.execute("SELECT * FROM users;")
        else:
            cursor.execute("SELECT * FROM users where pseudo='"+name+"';")

        records = cursor.fetchall()
    except Exception as e:
        print(e)

    list_user=[]
    for r in records:
        temp= {
        "pseudo": r.pseudo,
        "firstname": r.FirstName,
        "LastName": r.LastName,
        "private": r.private,
        "is_admin": r.is_admin
        }
        list_user.append(temp)
    
    return jsonify(list_user)


@app.route('/user', methods=['POST'])
def post_user():
    name = request.json.get("pseudo", None)
    password = request.json.get("password", None)
    firstname = request.json.get("firstname", None)
    lastname = request.json.get("lastname", None)

    try:
        conn = get_conn()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO users (pseudo, FirstName, LastName, mdp)
            VALUES ('"""+name+"""','"""+firstname+"""','"""+lastname+"""','"""+password+"""');
        """)
        cursor.commit()
        return jsonify({"State": 201})
    except Exception as e:
        print(e)

    return jsonify({"State": 400})

@app.route('/user', methods=['PUT'])
@jwt_required()
def put_user():
    private = request.json.get("private", None)
    password = request.json.get("password", None)
    firstname = request.json.get("firstname", None)
    lastname = request.json.get("lastname", None)

    current_user_id = get_jwt_identity()
    try:
        conn = get_conn()
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE users
            SET LastName = '"""+lastname+"""', FirstName = '"""+firstname+"""', mdp = '"""+password+"""' , private = '"""+private+"""'
            WHERE pseudo = '"""+current_user_id+"""'
        """)
        cursor.commit()
        return jsonify({"State": 201})
    except Exception as e:
        print(e)

    return jsonify({"State": 400})


@app.route('/user', methods=['DELETE'])
@jwt_required()
def delte_user():
    current_user_id = get_jwt_identity()

    try:
        conn = get_conn()
        cursor = conn.cursor()
        cursor.execute("""
            DELETE FROM users
            WHERE pseudo='"""+current_user_id+"""'
        """)
        cursor.commit()
        return jsonify({"State": 201})
    except Exception as e:
        print(e)

    return jsonify({"State": 400})


@app.route('/post', methods=['GET'])
@jwt_required()
def get_post():
    name = request.args.get('pseudo')
    records=[]
    try:
        conn = get_conn()
        cursor = conn.cursor()

        if name == None :
            cursor.execute("SELECT * FROM post;")
        elif not is_private(name):
            cursor.execute("SELECT * FROM post users='"+name+"';")

        records = cursor.fetchall()
    except Exception as e:
        print(e)

    list_post=[]
    for r in records:
        temp= {
        "id" : r.id,
        "post": r.comment,
        "author": r.users
        }
        list_post.append(temp)
    
    return jsonify(list_post)


@app.route('/post', methods=['POST'])
@jwt_required()
def post_post():
    comment = request.json.get("text", None)

    current_user_id = get_jwt_identity()
    try:
        conn = get_conn()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO post (users, comment)
            VALUES ('"""+current_user_id+"""','"""+comment+"""');
        """)
        cursor.commit()
        return jsonify({"State": 201})
    except Exception as e:
        print(e)

    return jsonify({"State": 400})

@app.route('/post', methods=['PUT'])
@jwt_required()
def put_post():
    uid = request.json.get("id", None)
    comment = request.json.get("text", None)

    current_user_id = get_jwt_identity()
    try:
        conn = get_conn()
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE post
            SET comment = '"""+comment+"""'
            WHERE users = '"""+current_user_id+"""' and id='"""+uid+"""'
        """)
        cursor.commit()
        return jsonify({"State": 201})
    except Exception as e:
        print(e)

    return jsonify({"State": 400})


@app.route('/post', methods=['DELETE'])
@jwt_required()
def delete_post():
    uid = request.json.get("id", None)

    current_user_id = get_jwt_identity()
    try:
        conn = get_conn()
        cursor = conn.cursor()
        cursor.execute("""
            DELETE FROM post
            WHERE users='"""+current_user_id+"""' and id= '"""+uid+"""'
        """)
        cursor.commit()
        return jsonify({"State": 201})
    except Exception as e:
        print(e)

    return jsonify({"State": 400})








@app.route('/search', methods=['GET'])
@jwt_required()
def search():
    results={"post":[], "pictures":[], "movies":[]}
    pseudo = request.json.get("pseudo", None)
    if not is_private(pseudo):
        records=[]
        try:
            conn = get_conn()
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM post users='"+pseudo+"';")
            cursor.commit()
            records = cursor.fetchall()
        except Exception as e:
            print(e)

        for r in records:
            temp= {
            "id" : r.id,
            "post": r.comment,
            "author": r.users
            }
            results["post"].append(temp)
    
    return jsonify(results)






@app.route("/initialisation")
def initialisation():
    try:
        conn = get_conn()
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE users (
                pseudo VARCHAR(255) NOT NULL PRIMARY KEY,
                FirstName VARCHAR(255) NOT NULL,
                LastName VARCHAR(255) NOT NULL,
                mdp VARCHAR(200) NOT NULL,
                private BIT NOT NULL DEFAULT 0,
                is_admin BIT NOT NULL DEFAULT 0
            );
        """)
        conn.commit()
    except Exception as e:
        print(e)

    try:
        conn = get_conn()
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE post (
                users VARCHAR(255) NOT NULL,
                id int IDENTITY(1,1) PRIMARY KEY,
                comment VARCHAR(255) NOT NULL,
                FOREIGN KEY (users) REFERENCES users(pseudo)
            );
        """)
        conn.commit()
    except Exception as e:
    # Table may already exist
        print(e)
    
    try:
        conn = get_conn()
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE pictures (
                users VARCHAR(255) NOT NULL,
                id int IDENTITY(1,1) PRIMARY KEY,
                name VARCHAR(255) NOT NULL,
                FOREIGN KEY (users) REFERENCES users(pseudo)
            );
        """)
        conn.commit()
    except Exception as e:
    # Table may already exist
        print(e)

    try:
        conn = get_conn()
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE video (
                users VARCHAR(255) NOT NULL,
                id int IDENTITY(1,1) PRIMARY KEY,
                name VARCHAR(255) NOT NULL,
                FOREIGN KEY (users) REFERENCES users(pseudo)
            );
        """)
        conn.commit()
    except Exception as e:
    # Table may already exist
        print(e)

    try:
        conn = get_conn()
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE comment (
                users VARCHAR(255) NOT NULL,
                post int,
                pictures int,
                video int,
                id int IDENTITY(1,1) PRIMARY KEY,
                commant VARCHAR(255) NOT NULL,
                FOREIGN KEY (users) REFERENCES users(pseudo),
                FOREIGN KEY (post) REFERENCES post(id),
                FOREIGN KEY (pictures) REFERENCES pictures(id),
                FOREIGN KEY (video) REFERENCES video(id)
            );
        """)
        conn.commit()
    except Exception as e:
    # Table may already exist
        print(e)

    return "<h1>Initialisation terminé</h1>"



if __name__ == "__main__":
    app.run(debug=True)



def is_private(name):
    records=[]
    try:
        conn = get_conn()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM user pseudo='"+name+"';")
        records = cursor.fetchall()
    except Exception as e:
        print(e)

    return records[0].private

def is_admin(name):
    records=[]
    try:
        conn = get_conn()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM user pseudo='"+name+"';")
        records = cursor.fetchall()
    except Exception as e:
        print(e)

    return records[0].pris_admin


def get_conn():
    conn = pyodbc.connect(connection_string)
    return conn

