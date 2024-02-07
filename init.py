from flask import Flask, request, jsonify
from flask_jwt_extended import JWTManager
from datetime import timedelta
from flask_jwt_extended import create_access_token
from flask_jwt_extended import jwt_required, get_jwt_identity
from flask_cors import CORS

from flask_swagger_ui import get_swaggerui_blueprint

from azure.storage.blob import BlobServiceClient

import pyodbc, struct ,os
import json



db = os.environ["AZURE_SQL_DB"]
dbname = os.environ["AZURE_SQL_DBNAME"]
logindb = os.environ["AZURE_SQL_LOGINDB"]
passworddb = os.environ["AZURE_SQL_PASSWORDDB"]
ACCESS_EXPIRES = timedelta(hours=1)


connection_string = "Driver={ODBC Driver 18 for SQL Server};Server=tcp:"+db+".database.windows.net,1433;Database="+dbname+";Uid="+logindb+";Pwd="+passworddb+";Encrypt=yes;TrustServerCertificate=no;Connection Timeout=30;"
app = Flask(__name__)
cors = CORS(app, resources={r"/*": {"Access-Control-Allow-Origin": "*"}})

picture_container_name = "pictures"
video_container_name = "video"

blob_service_client = BlobServiceClient.from_connection_string(conn_str=os.getenv('AZURE_STORAGE_CONNECTION_STRING'))
try:
    picture_container_client = blob_service_client.get_container_client(container=picture_container_name)
    picture_container_client.get_container_properties()
except Exception as e:
    picture_container_client = blob_service_client.create_container(picture_container_name)

try:
    video_container_client = blob_service_client.get_container_client(container=video_container_name)
    video_container_client.get_container_properties()
except Exception as e:
    video_container_client = blob_service_client.create_container(video_container_name)

SWAGGER_URL = '/api/docs'  # URL for exposing Swagger UI (without trailing '/')
API_URL = '/static/swagger.json'  # Our API url (can of course be a local resource)

# Call factory function to create our blueprint
swaggerui_blueprint = get_swaggerui_blueprint(
    SWAGGER_URL,  # Swagger UI static files will be mapped to '{SWAGGER_URL}/dist/'
    API_URL,
    config={  # Swagger UI config overrides
        'app_name': "Test application"
    },
)

app.register_blueprint(swaggerui_blueprint, url_prefix=SWAGGER_URL)

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
            cursor.execute("SELECT * FROM users where pseudo = \'"+name+"\';")

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

@app.route('/picture', methods=['POST'])
@jwt_required()
def post_picture():
    current_user_id = get_jwt_identity()
    try:
        fichier = request.files['file']
        nomfichier = fichier.filename.replace(" ", "")
        blob_client = picture_container_client.get_blob_client(nomfichier)
        blob_client.upload_blob(nomfichier)
        name = "https://mediasocialstorageag37.blob.core.windows.net/pictures/" + nomfichier
        conn = get_conn()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO pictures (name, users)
            VALUES ('"""+name+"""','"""+current_user_id+"""');
        """)
        cursor.commit()
        
        return jsonify({"State": 201})
    except Exception as e:
        print(e)
        return jsonify({"State": 400,
                        "error": str(e)})

@app.route('/picture', methods=['GET'])
@jwt_required()
def get_picture():
    name = request.args.get('pseudo')
    records=[]
    current_user_id = get_jwt_identity()
    try:
        conn = get_conn()
        cursor = conn.cursor()

        if name == None:
            cursor.execute("SELECT * FROM pictures p INNER JOIN users u ON u.pseudo=p.users WHERE u.private=0;")
        elif is_exist(name) and (not is_private(name) or name == current_user_id):
            cursor.execute("SELECT * FROM pictures users='"+name+"';")
        else:
            return jsonify({"Error": "User is private"})

        records = cursor.fetchall()
    except Exception as e:
        print(e)

    list_post=[]
    for r in records:
        temp= {
        "id" : r.id,
        "post": r.name,
        "author": r.users
        }
        list_post.append(temp)
    
    return jsonify(list_post)
    
@app.route('/picture', methods=['DELETE'])
@jwt_required()
def delete_picture():
    uid = request.args.get("id", None)

    current_user_id = get_jwt_identity()
    try:
        conn = get_conn()
        cursor = conn.cursor()
        cursor.execute("""
            DELETE FROM pictures
            WHERE users='"""+current_user_id+"""' and id= '"""+uid+"""'
        """)
        cursor.commit()
        return jsonify({"State": 201})
    except Exception as e:
        print(e)
        return jsonify({"State": 400,
                    "error": str(e)})
    
@app.route('/video', methods=['POST'])
@jwt_required()
def post_video():
    current_user_id = get_jwt_identity()
    try:
        fichier = request.files['file']
        nomfichier = fichier.filename.replace(" ", "")
        blob_client = video_container_client.get_blob_client(nomfichier)
        blob_client.upload_blob(nomfichier)
        name = "https://mediasocialstorageag37.blob.core.windows.net/video/" + nomfichier
        conn = get_conn()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO video (name, users)
            VALUES ('"""+name+"""','"""+current_user_id+"""');
        """)
        cursor.commit()
        
        return jsonify({"State": 201})
    except Exception as e:
        print(e)
        return jsonify({"State": 400,
                    "error": str(e)})
        
@app.route('/video', methods=['GET'])
@jwt_required()
def get_video():
    name = request.args.get('pseudo')

    current_user_id = get_jwt_identity()
    records=[]
    try:
        conn = get_conn()
        cursor = conn.cursor()

        if name == None :
            cursor.execute("SELECT * FROM video o INNER JOIN users u ON u.pseudo=o.users WHERE u.private=0;")
        elif is_exist(name) and (not is_private(name) or name == current_user_id):
            cursor.execute("SELECT * FROM video users='"+name+"';")
        else:
            return jsonify({"Error": "User is private"})

        records = cursor.fetchall()
    except Exception as e:
        print(e)

    list_post=[]
    for r in records:
        temp= {
        "id" : r.id,
        "post": r.name,
        "author": r.users
        }
        list_post.append(temp)
    
    return jsonify(list_post)
    
@app.route('/video', methods=['DELETE'])
@jwt_required()
def delete_video():
    uid = request.args.get("id", None)

    current_user_id = get_jwt_identity()
    try:
        conn = get_conn()
        cursor = conn.cursor()
        cursor.execute("""
            DELETE FROM video
            WHERE users='"""+current_user_id+"""' and id= '"""+uid+"""'
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

    current_user_id = get_jwt_identity()
    try:
        conn = get_conn()
        cursor = conn.cursor()

        if name == None :
            cursor.execute("SELECT * FROM post p INNER JOIN users u ON u.pseudo=p.users WHERE u.private=0;")
        elif is_exist(name) and (not is_private(name) or name == current_user_id):
            cursor.execute("SELECT * FROM post WHERE users='"+name+"';")
        else:
            return jsonify({"Error": "User is private"})
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
    uid = request.args.get("id", None)

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


@app.route('/comment', methods=['GET'])
@jwt_required()
def get_comment():
    name = request.args.get('pseudo')

    current_user_id = get_jwt_identity()
    records=[]
    try:
        conn = get_conn()
        cursor = conn.cursor()

        if name == None :
            cursor.execute("SELECT * FROM comment c INNER JOIN users u ON u.pseudo=c.users WHERE u.private=0;;")
        elif is_exist(name) and (not is_private(name) or name == current_user_id):
            cursor.execute("SELECT * FROM comment users='"+name+"';")

        records = cursor.fetchall()
    except Exception as e:
        print(e)

    list_comment=[]
    for r in records:
        temp= {
        "id" : r.id,
        "post_id" : r.post,
        "pictures_id" : r.pictures,
        "video_id": r.video,
        "comment": r.text_comment,
        "author": r.users
        }
        list_comment.append(temp)
    
    return jsonify(list_comment)


@app.route('/comment', methods=['POST'])
@jwt_required()
def post_comment():
    comment = str(request.json.get("text", None))
    type_post = str(request.json.get("type", None))
    uid = str(request.json.get("id", None))

    current_user_id = get_jwt_identity()
    try:
        conn = get_conn()
        cursor = conn.cursor()
        if type_post == "video":
            cursor.execute("""
                INSERT INTO comment (users, text_comment, video)
                VALUES ('"""+current_user_id+"""','"""+comment+"""','"""+uid+"""');
            """)
        elif type_post == "pictures":
            cursor.execute("""
                INSERT INTO comment (users, text_comment, pictures)
                VALUES ('"""+current_user_id+"""','"""+comment+"""','"""+uid+"""');
            """)
        elif type_post == "post":
            cursor.execute("""
                INSERT INTO comment (users, text_comment, post)
                VALUES ('"""+current_user_id+"""','"""+comment+"""','"""+uid+"""');
            """)
        cursor.commit()
        return jsonify({"State": 201})
    except Exception as e:
        print(e)

    return jsonify({"State": 400})

@app.route('/comment', methods=['PUT'])
@jwt_required()
def put_comment():
    uid = request.json.get("id", None)
    comment = request.json.get("text", None)

    current_user_id = get_jwt_identity()
    try:
        conn = get_conn()
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE comment
            SET text_comment = '"""+comment+"""'
            WHERE users = '"""+current_user_id+"""' and id='"""+uid+"""'
        """)
        cursor.commit()
        return jsonify({"State": 201})
    except Exception as e:
        print(e)

    return jsonify({"State": 400})


@app.route('/comment', methods=['DELETE'])
@jwt_required()
def delete_comment():
    uid = request.args.get("id", None)

    current_user_id = get_jwt_identity()
    try:
        conn = get_conn()
        cursor = conn.cursor()
        if is_admin(current_user_id):
            cursor.execute("""
                DELETE FROM comment
                WHERE id='"""+uid+"""'
            """)
        else:
            cursor.execute("""
                DELETE FROM comment
                WHERE users='"""+current_user_id+"""' and id='"""+uid+"""'
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
    pseudo = request.args.get("pseudo", None)

    current_user_id
    if is_exist(pseudo) and (not is_private(pseudo) or pseudo == current_user_id):
        records=[]
        try:
            conn = get_conn()
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM post WHERE users='"+pseudo+"';")
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

        try:
            conn = get_conn()
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM pictures WHERE users='"+pseudo+"';")
            records = cursor.fetchall()
        except Exception as e:
            print(e)

        for r in records:
            temp= {
            "id" : r.id,
            "name": r.name,
            "author": r.users
            }
            results["pictures"].append(temp)
        
        try:
            conn = get_conn()
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM video WHERE users='"+pseudo+"';")
            records = cursor.fetchall()
        except Exception as e:
            print(e)

        for r in records:
            temp= {
            "id" : r.id,
            "name": r.name,
            "author": r.users
            }
            results["movies"].append(temp)
        return jsonify(results)
    
    else:
        return jsonify({"Error": "User is private or doesn't exist"})



@app.route("/initialisation", methods=['GET'])
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
                text_comment VARCHAR(255) NOT NULL,
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


def is_exist(name):
    records=[]
    try:
        conn = get_conn()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE pseudo='"+name+"';")
        records = cursor.fetchall()
    except Exception as e:
        print(e)
    if len(records)<=0:
        return False
    else:
        return True



def is_private(name):
    records=[]
    try:
        conn = get_conn()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE pseudo='"+name+"';")
        records = cursor.fetchall()
    except Exception as e:
        print(e)

    return records[0].private

def is_admin(name):
    records=[]
    try:
        conn = get_conn()
        cursor = conn.cursor()
        cursor.execute("""SELECT * FROM users WHERE pseudo='"""+name+"""';""")
        records = cursor.fetchall()
    except Exception as e:
        print(e)

    return records[0].is_admin


def get_conn():
    conn = pyodbc.connect(connection_string)
    return conn

