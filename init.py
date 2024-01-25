from flask import Flask
import pyodbc, struct ,os
from azure import identity

# connection_string = os.environ["AZURE_SQL_CONNECTIONSTRING"]
connection_string = "Driver={ODBC Driver 13 for SQL Server};Server=tcp:mediadb4deas.database.windows.net,1433;Database=mediasocial;Uid=@mediadb4deas;Pwd=/Password37;Encrypt=yes;TrustServerCertificate=no;"
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
        print(e)
    return connection_string

if __name__ == "__main__":
    app.run(debug=True)


def get_conn():
    credential = identity.DefaultAzureCredential(exclude_interactive_browser_credential=False)
    token_bytes = credential.get_token("https://database.windows.net/.default").token.encode("UTF-16-LE")
    token_struct = struct.pack(f'<I{len(token_bytes)}s', len(token_bytes), token_bytes)
    SQL_COPT_SS_ACCESS_TOKEN = 1256  # This connection option is defined by microsoft in msodbcsql.h
    conn = pyodbc.connect(connection_string, attrs_before={SQL_COPT_SS_ACCESS_TOKEN: token_struct})
    return conn