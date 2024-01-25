from flask import Flask
import pyodbc, struct ,os
from azure import identity

connection_string = os.environ["AZURE_SQL_CONNECTIONSTRING"]
app = Flask(__name__)



@app.route("/")
def index():
    return "<h1>Hello Azure!</h1>"

if __name__ == "__main__":
    conn = get_conn()
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE user (
            pseudo varchar(255) NOT NULL PRIMARY KEY,
            FirstName varchar(255) NOT NULL,
            LastName varchar(255) NOT NULL,
            mdp varchar(255) NOT NULL,
            private BIT NOT NULL DEFAULT 0,
            is_admin BIT NOT NULL DEFAULT 0,
        );
    """)

    conn.commit()
    app.run(debug=True)


def get_conn():
    credential = identity.DefaultAzureCredential(exclude_interactive_browser_credential=False)
    token_bytes = credential.get_token("https://database.windows.net/.default").token.encode("UTF-16-LE")
    token_struct = struct.pack(f'<I{len(token_bytes)}s', len(token_bytes), token_bytes)
    SQL_COPT_SS_ACCESS_TOKEN = 1256  # This connection option is defined by microsoft in msodbcsql.h
    conn = pyodbc.connect(connection_string, attrs_before={SQL_COPT_SS_ACCESS_TOKEN: token_struct})
    return conn