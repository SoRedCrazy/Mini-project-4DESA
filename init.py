from flask import Flask
import pyodbc, struct ,os
from azure import identity

connection_string = os.environ["AZURE_SQL_CONNECTIONSTRING"]
app = Flask(__name__)

@app.route("/")
def index():
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
    # Table may already exist
       return str(e)
    return connection_string

if __name__ == "__main__":
    app.run(debug=True)


def get_conn():
    conn = pyodbc.connect(connection_string)
    return conn