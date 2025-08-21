import azure.functions as func
import json
import bcrypt
from . import get_db_connection, getjwt 

app = func.FunctionApp()

@app.route(route="login")
def login(req: func.HttpRequest) -> func.HttpResponse:
    try:
        # Parse the JSON body, handle possible exceptions for invalid JSON
        try:
            rbody = req.get_json()
        except ValueError:
            return func.HttpResponse("Request body must be valid JSON", status_code=400)

        if not rbody:
            return func.HttpResponse("Request body cannot be empty", status_code=400)

        email = rbody.get("email")
        if not email:
            return func.HttpResponse("Missing email", status_code=400)

        password = rbody.get("password")
        if not password:
            return func.HttpResponse("Missing password", status_code=400)

        print(f"Debug: Received {email}/{password}")
        connection = get_db_connection()
        print(f"Debug: Database connected: {connection.is_connected()}")
        if connection.is_connected():
            query = "SELECT id, password, role, admin_id FROM users WHERE email = %s"
            cursor = connection.cursor()
            cursor.execute(query, (email,))
            result = cursor.fetchone()
            print(f"Debug: Query result: {result}")
            connection.close()
            if result:
                user_id, password_hash, role = result[0], result[1], result
                admin_id = result if len(result) > 3 else None
                print(f"Debug: Comparing passwords")
                if bcrypt.checkpw(password.encode('utf-8'), password_hash.encode('utf-8')):
                    print(f"Debug: Password match, generating JWT")
                    jwt_data = getjwt(email, user_id, role, admin_id)
                    return func.HttpResponse(json.dumps(jwt_data), status_code=200, mimetype="application/json")
                else:
                    print(f"Debug: Password mismatch")
                    return func.HttpResponse("Invalid password!", status_code=401)
            else:
                print(f"Debug: User not found")
                return func.HttpResponse("User not found", status_code=401)
        else:
            print(f"Debug: Failed to connect to DB")
            return func.HttpResponse("Failed to connect DB", status_code=500)
    except Exception as e:
        print(f"Error: {e}")
        return func.HttpResponse(str(e), status_code=500)
