from flask import Flask
import pyodbc, struct ,os
from azure import identity

db = os.environ["AZURE_SQL_DB"]
dbname = os.environ["AZURE_SQL_DBNAME"]
logindb = os.environ["AZURE_SQL_LOGINDB"]
passworddb = os.environ["AZURE_SQL_PASSWORDDB"]

connection_string = "Driver={ODBC Driver 18 for SQL Server};Server=tcp:"+db+".database.windows.net,1433;Database="+dbname+";Uid="+logindb+";Pwd="+passworddb+";Encrypt=yes;TrustServerCertificate=no;Connection Timeout=30;"
app = Flask(__name__)

@app.route("/")
def index():
    return "hello azure"

if __name__ == "__main__":
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
    app.run(debug=True)


def get_conn():
    conn = pyodbc.connect(connection_string)
    return conn