import base64
import json
import os
import time
import uuid
from datetime import datetime, timedelta

import azure.functions as func
import bcrypt
import bcrypt
password = "admin123".encode('utf-8')
hashed = bcrypt.hashpw(password, bcrypt.gensalt())
print(hashed.decode('utf-8'))  # Copy this value into the INSERT statement
import mysql.connector
import requests
import jwt  # For JWT validation

from util import (
    download_pdf,
    send_email,
    getjwt,
    fetchimgs,
    upload_pdf,
    download_aireport,
    download_medioimages,
    upload_images,
    validate_jwt,
    get_user_role_and_admin,
    get_db_connection,
)

app = func.FunctionApp(http_auth_level=func.AuthLevel.FUNCTION)  # Require keys/JWT

# Updated /putimages with auth
@app.route(route="putimages")
def putimages(req: func.HttpRequest) -> func.HttpResponse:
    _ = validate_jwt(req)  # Basic auth check
    attachment_path = "/tmp/"
    bid = req.params.get('bid')
    mrn = req.params.get('mrn')

    if download_medioimages(bid=bid, mrn=mrn, download_path=attachment_path):
        upload_images(attachment_path, bid)
        return func.HttpResponse("Images Uploaded", status_code=200, mimetype="application/json")
    else:
        return func.HttpResponse("Failed to upload images", status_code=500, mimetype="application/json")

# Updated /enableimages with auth
@app.route(route="enableimages")
def enableimages(req: func.HttpRequest) -> func.HttpResponse:
    _ = validate_jwt(req)
    bid = req.params.get('bid')
    connection = get_db_connection()

    if connection.is_connected():
        query = "UPDATE pbooking SET images=%s WHERE id=%s"
        values = (1, bid)
        cursor = connection.cursor()
        cursor.execute(query, values)
        connection.commit()
        connection.close()
        return func.HttpResponse("Images Status Updated", status_code=200, mimetype="application/json")

# Updated /enableaireport with auth
@app.route(route="enableaireport")
def enableaireport(req: func.HttpRequest) -> func.HttpResponse:
    _ = validate_jwt(req)
    bid = req.params.get('bid')
    connection = get_db_connection()

    if connection.is_connected():
        query = "UPDATE pbooking SET aireport=%s WHERE id=%s"
        values = (1, bid)
        cursor = connection.cursor()
        cursor.execute(query, values)
        connection.commit()
        connection.close()
        return func.HttpResponse("AI Status Updated", status_code=200, mimetype="application/json")

# Updated /putaireport with auth
@app.route(route="putaireport")
def putaireport(req: func.HttpRequest) -> func.HttpResponse:
    _ = validate_jwt(req)
    attachment_path = "/tmp/aireport.pdf"
    bid = req.params.get('bid')
    mrn = req.params.get('mrn')

    if download_aireport(bid=bid, mrn=mrn, download_path=attachment_path):
        with open(attachment_path, "rb") as pdf_file:
            upload_pdf(blob_name=bid + ".pdf", data=pdf_file)
        return func.HttpResponse("PDF Uploaded", status_code=200, mimetype="application/json")
    else:
        return func.HttpResponse("Failed to upload PDF", status_code=500, mimetype="application/json")

# Updated /sendaireport with auth
@app.route(route="sendaireport")
def sendaireport(req: func.HttpRequest) -> func.HttpResponse:
    _ = validate_jwt(req)
    bid = req.params.get('bid') + ".pdf"
    recipient = req.params.get('recipient')
    download_pdf(blob_name=bid)
    send_email("AI Report", f"Attached is the AI report of patient", recipient)
    return func.HttpResponse("PDF Sent", status_code=200, mimetype="application/json")

# Updated /getaireport with auth
@app.route(route="getaireport")
def getaireport(req: func.HttpRequest) -> func.HttpResponse:
    user = validate_jwt(req)
    role, admin_id = get_user_role_and_admin(user['username'])
    bid = req.params.get('bid')
    connection = get_db_connection()
    cursor = connection.cursor()
    query = "SELECT hospital_id FROM pbooking WHERE id=%s"
    cursor.execute(query, (bid + ".pdf",))
    hosp = cursor.fetchone()[0]
    if hosp != admin_id and role != 'superadmin':
        return func.HttpResponse("Forbidden", status_code=403)
    attachment_path = "/tmp/aireport.pdf"
    download_pdf(blob_name=bid + ".pdf")
    with open(attachment_path, "rb") as pdf_file:
        pdf_data = pdf_file.read()
    return func.HttpResponse(
        body=pdf_data,
        status_code=200,
        mimetype="application/pdf",
        headers={"Content-Disposition": f"attachment; filename=aireport.pdf"},
    )

# Updated /getimages with auth
@app.route(route="getimages")
def getimages(req: func.HttpRequest) -> func.HttpResponse:
    user = validate_jwt(req)
    role, admin_id = get_user_role_and_admin(user['username'])
    bid = req.params.get('bid')
    connection = get_db_connection()
    cursor = connection.cursor()
    query = "SELECT hospital_id FROM pbooking WHERE id=%s"
    cursor.execute(query, (bid,))
    hosp = cursor.fetchone()[0]
    if hosp != admin_id and role != 'superadmin':
        return func.HttpResponse("Forbidden", status_code=403)
    blobs = fetchimgs(bid)
    images = [{"name": blob["name"], "data": base64.b64encode(blob["data"]).decode("utf-8")} for blob in blobs]
    return func.HttpResponse(json.dumps(images), status_code=200, mimetype="application/json")

# Updated /aireport2 with auth
@app.route(route="aireport2")
def aireport2(req: func.HttpRequest) -> func.HttpResponse:
    _ = validate_jwt(req)
    mrn = req.params.get('mrn')
    url = f"https://remidio-backend-germany.appspot.com/api/gateway/getPatientWithLastExam/siteCustomId/213321/{mrn}"
    session = requests.Session()
    headers = {
        "clientName": "PACS_GATEWAY",
        "clientIdentificationToken": os.getenv('CIT'),
        "clientAuthToken": os.getenv('CAT')
    }
    session.headers.update(headers)
    response = session.get(url)
    if response.status_code == 200:
        try:
            pdf = response.json()["data"]["aiReport"]["path"]
            return func.HttpResponse(pdf)
        except Exception:
            return func.HttpResponse("AI Report unavailable", status_code=500, mimetype="application/json")
    else:
        return func.HttpResponse("AI Report unavailable", status_code=500, mimetype="application/json")

# Updated /aireport with auth
@app.route(route="aireport")
def aireport(req: func.HttpRequest) -> func.HttpResponse:
    _ = validate_jwt(req)
    connection = get_db_connection()
    bookingref = req.params.get('bookingref') or req.get_json().get('bookingref')
    if connection.is_connected():
        cursor = connection.cursor()
        query = f"select patient_basic_info.id_number from booking left JOIN patient_basic_info ON booking.patient_nationalid = patient_basic_info.id_number where booking.booking_ref='{bookingref}'"
        cursor.execute(query)
        results = cursor.fetchone()
        mrn = results[0]
        connection.close()
        url = f"https://remidio-backend-germany.appspot.com/api/gateway/getPatientWithLastExam/siteCustomId/213321/{mrn}"
        session = requests.Session()
        headers = {
            "clientName": "PACS_GATEWAY",
            "clientIdentificationToken": os.getenv('CIT'),
            "clientAuthToken": os.getenv('CAT')
        }
        session.headers.update(headers)
        response = session.get(url)
        if response.status_code == 200:
            pdf = response.json()["data"]["aiReport"]["path"]
            return func.HttpResponse(pdf)
        else:
            # Your original token refresh code
            session = requests.Session()
            headers = {
                "clientName": "PACS_GATEWAY",
                "clientIdentificationToken": os.getenv('CIT')
            }
            session.headers.update(headers)
            response = session.post("https://remidio-backend-germany.appspot.com/api/user/loginUser", json={
                "emailAddress": "drboitshepo2019@gmail.com",
                "password": "Mychrist@1"
            })
            btoken = response.json()["data"]
            headers = {
                "Authorization": f"Bearer {btoken}",
                "Content-Type": "application/json",
                "clientName": "PACS_GATEWAY",
                "clientIdentificationToken": os.getenv('CIT')
            }
            session.headers.update(headers)
            response = session.get("https://remidio-backend-germany.appspot.com/api/gateway/getAuthToken")
            CAT = response.json()["data"]
            headers = {
                "clientName": "PACS_GATEWAY",
                "clientIdentificationToken": os.getenv('CIT'),
                "clientAuthToken": CAT
            }
            session.headers.update(headers)
            response = session.get(url)
            pdf = response.json()["data"]["aiReport"]["path"]
            return func.HttpResponse(pdf)
    else:
        return func.HttpResponse("Failed", status_code=500)

# Updated /patients with auth and hospital filter
@app.route(route="patients")
def patients(req: func.HttpRequest) -> func.HttpResponse:
    user = validate_jwt(req)
    role, admin_id = get_user_role_and_admin(user['username'])
    connection = get_db_connection()
    if connection.is_connected():
        cursor = connection.cursor()
        if role == 'superadmin':
            query = "SELECT mrn, firstname, lastname, gender, dob, phone, email FROM patient"
            cursor.execute(query)
        else:
            query = "SELECT mrn, firstname, lastname, gender, dob, phone, email FROM patient WHERE hospital_id = %s"
            cursor.execute(query, (admin_id,))
        results = cursor.fetchall()
        patients = []
        for patient in results:
            date_obj = datetime.strptime(str(patient[4]), "%Y-%m-%d")
            date_str = date_obj.strftime("%B %d, %Y")
            patients.append({
                "name": patient[1] + " " + patient[2],
                "mrn": patient[0],
                "gender": patient[3],
                "dob": date_str,
                "phone": patient[5],
                "email": patient[6]
            })
        connection.close()
        return func.HttpResponse(json.dumps(patients), status_code=200, mimetype="application/json")

# Updated /bookings with auth and hospital filter
@app.route(route="bookings")
def bookings(req: func.HttpRequest) -> func.HttpResponse:
    user = validate_jwt(req)
    role, admin_id = get_user_role_and_admin(user['username'])
    mrn = req.params.get('mrn')
    connection = get_db_connection()
    if connection.is_connected():
        cursor = connection.cursor()
        if role == 'superadmin':
            query = "SELECT * FROM pbooking WHERE mrn=%s"
            cursor.execute(query, (int(mrn),))
        else:
            query = "SELECT * FROM pbooking WHERE mrn=%s AND hospital_id=%s"
            cursor.execute(query, (int(mrn), admin_id))
        results = cursor.fetchall()
        bookings = []
        for booking in results:
            date_obj = datetime.strptime(str(booking[7]), "%Y-%m-%d %H:%M:%S")
            date_str = date_obj.strftime("%B %d, %Y at %I:%M %p")
            bookings.append({
                "id": booking[0],
                "mrn": booking[1],
                "height": booking[2],
                "weight": booking[3],
                "bp": booking[4],
                "hba1c": booking[5],
                "rbg": booking[6],
                "created_at": date_str,
                "aireport": bool(booking[8]),
                "imagesexists": bool(booking[9]),
                "appointment_type": booking[10] if len(booking) > 10 else None,  # Adjust indices based on schema
                "specialist_id": booking[11],
                "status": booking[12],
                "diagnosis": booking[13],
                "specialist_comment": booking[14]
            })
        connection.close()
        return func.HttpResponse(json.dumps(bookings), status_code=200, mimetype="application/json")

# addremidiopatient (internal, no auth needed)
def addremidiopatient(mrn):
    connection = get_db_connection()
    if connection.is_connected():
        cursor = connection.cursor()
        query = "select * from patient WHERE mrn=%s"
        cursor.execute(query, (int(mrn),))
        patient = cursor.fetchone()
        connection.close()
        fname = patient[1]
        lname = patient[2]
        date_obj = datetime.strptime(str(patient[3]), "%Y-%m-%d")
        dob = int(date_obj.timestamp() * 1000)
        gender = patient[4]

    creatingUserId = "5239911615561728"
    examLocalId = str(uuid.uuid4())
    examDate = int(time.time() * 1000)
    deviceType = ["FOP"]
    patient = {
        "mrn": str(mrn),
        "firstName": fname,
        "lastName": lname,
        "dateOfBirth": dob,
        "gender": gender
    }
    orderingProvider = {
        "firstName": "Default",
        "lastName": "Provider",
        "email": "defaultprovider@domain.com"
    }
    url = "https://remidio-backend-germany.appspot.com/api/gateway/createPatientExam"
    payload = {
        "patient": patient,
        "orderingProvider": orderingProvider,
        "creatingUserId": creatingUserId,
        "examLocalId": examLocalId,
        "examDate": examDate,
        "deviceType": deviceType
    }
    headers = {
        "clientName": "PACS_GATEWAY",
        "clientIdentificationToken": os.getenv('CIT'),
        "clientAuthToken": os.getenv('CAT')
    }
    return requests.post(url, json=payload, headers=headers)

# Updated /addpatient with auth and hospital_id
@app.route(route="addpatient")
def addpatient(req: func.HttpRequest) -> func.HttpResponse:
    user = validate_jwt(req)
    role, admin_id = get_user_role_and_admin(user['username'])
    if role not in ['technician', 'doctor']:
        return func.HttpResponse("Forbidden", status_code=403)
    req_body = req.get_json()
    fname = req_body.get("fname")
    lname = req_body.get("lname")
    gender = req_body.get("gender")
    dob = req_body.get("dob")
    phone = req_body.get("phone") or None
    email = req_body.get("email") or None
    connection = get_db_connection()
    if connection.is_connected():
        query = "INSERT INTO patient (firstname, lastname, dob, gender, phone, email, hospital_id) VALUES (%s, %s, %s, %s, %s, %s, %s)"
        cursor = connection.cursor()
        cursor.execute(query, (fname, lname, dob, gender, phone, email, admin_id))
        connection.commit()
        mrn = cursor.lastrowid
        connection.close()
        if addremidiopatient(mrn).status_code == 200:
            return func.HttpResponse(str(mrn), status_code=200, mimetype="application/json")
        else:
            return func.HttpResponse("Failed to create remidio patient", status_code=500, mimetype="application/json")
    else:
        return func.HttpResponse("Failed to connect DB", status_code=500, mimetype="application/json")

# Updated /updatepatient with auth
# (As in previous)

# Updated /deletepatient with auth
# (As in previous)

# Updated /createbooking with auth
@app.route(route="createbooking")
def createbooking(req: func.HttpRequest) -> func.HttpResponse:
    user = validate_jwt(req)
    role, admin_id = get_user_role_and_admin(user['username'])
    if role not in ['technician', 'doctor']:
        return func.HttpResponse("Forbidden", status_code=403)
    mrn = req.params.get('mrn')
    rbody = req.get_json()
    appointment_type = rbody.get('appointment_type')
    specialist_id = rbody.get('specialist_id')
    rpatient = addremidiopatient(mrn)
    if rpatient.status_code == 200:
        id = rpatient.json()["data"]["examDetails"]["id"]
        connection = get_db_connection()
        query = "INSERT INTO pbooking (id, mrn, height, weight, bp, hba1c, rbg, hospital_id, appointment_type, specialist_id) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"
        cursor = connection.cursor()
        cursor.execute(query, (id, mrn, rbody["height"], rbody["weight"], rbody["bp"], rbody["hba1c"], rbody["rbg"], admin_id, appointment_type, specialist_id))
        connection.commit()
        # Conditions and medications (original logic)
        query = "INSERT INTO medcondition (pbid, name, status) VALUES (%s, %s, %s)"
        conditions = [(id, c["name"], c["status"]) for c in rbody["conditions"]]
        cursor.executemany(query, conditions)
        connection.commit()
        query = "INSERT INTO medication (pbid, name, dosage) VALUES (%s, %s, %s)"
        medications = [(id, m["name"], m["dosage"]) for m in rbody["medications"]]
        cursor.executemany(query, medications)
        connection.commit()
        if role == 'technician':
            update_query = "UPDATE pbooking SET status='pending' WHERE id=%s"
            cursor.execute(update_query, (id,))
            connection.commit()
        connection.close()
        return func.HttpResponse(str(mrn), status_code=200, mimetype="application/json")
    else:
        return func.HttpResponse(f"Failed to create remidio patient: {rpatient.text}", status_code=500, mimetype="application/json")

# Updated /dashboardstats with auth
# (As in previous)

# Updated /signup with auth (if needed, but original is open for new users)

# Updated /user with auth
@app.route(route="user")
def user(req: func.HttpRequest) -> func.HttpResponse:
    _ = validate_jwt(req)
    email = req.params.get("email")
    connection = get_db_connection()
    if connection.is_connected():
        query = "SELECT id, firstname, lastname, role, admin_id FROM users WHERE email = %s"
        cursor = connection.cursor()
        cursor.execute(query, (email,))
        userinfo = cursor.fetchone()
        connection.close()
        if userinfo:
            return func.HttpResponse(json.dumps({
                "id": userinfo[0],
                "username": email,
                "email": email,
                "first_name": userinfo[1],
                "last_name": userinfo[2],
                "role": userinfo[3],
                "admin_id": userinfo[4]
            }), status_code=200, mimetype="application/json")
        else:
            return func.HttpResponse("User not found", status_code=401)
    else:
        return func.HttpResponse("Failed to connect DB", status_code=500)

# New: Superadmin creates Admin
@app.route(route="create_admin")
def create_admin(req: func.HttpRequest) -> func.HttpResponse:
    user = validate_jwt(req)
    role, _ = get_user_role_and_admin(user['username'])
    if role != 'superadmin':
        return func.HttpResponse("Forbidden", status_code=403)
    
    req_body = req.get_json()
    email = req_body['email']
    password_hash = bcrypt.hashpw(req_body['password'].encode('utf-8'), bcrypt.gensalt())
    
    connection = get_db_connection()
    cursor = connection.cursor()
    query = "INSERT INTO users (email, password, role) VALUES (%s, %s, %s)"
    cursor.execute(query, (email, password_hash, 'admin'))
    connection.commit()
    admin_id = cursor.lastrowid
    connection.close()
    return func.HttpResponse(str(admin_id), status_code=200)

# New: Superadmin creates Specialist/Technician and assigns to Admin
@app.route(route="create_user")
def create_user(req: func.HttpRequest) -> func.HttpResponse:
    user = validate_jwt(req)
    role, _ = get_user_role_and_admin(user['username'])
    if role != 'superadmin':
        return func.HttpResponse("Forbidden", status_code=403)
    
    req_body = req.get_json()
    email = req_body['email']
    password_hash = bcrypt.hashpw(req_body['password'].encode('utf-8'), bcrypt.gensalt())
    user_role = req_body['role']  # 'specialist' or 'technician'
    assign_admin_id = req_body['admin_id']
    
    connection = get_db_connection()
    cursor = connection.cursor()
    query = "INSERT INTO users (email, password, role, admin_id) VALUES (%s, %s, %s, %s)"
    cursor.execute(query, (email, password_hash, user_role, assign_admin_id))
    connection.commit()
    user_id = cursor.lastrowid
    connection.close()
    return func.HttpResponse(str(user_id), status_code=200)

# New: Admin creates Doctor (assigned to self)
@app.route(route="create_doctor")
def create_doctor(req: func.HttpRequest) -> func.HttpResponse:
    user = validate_jwt(req)
    role, admin_id = get_user_role_and_admin(user['username'])
    if role != 'admin':
        return func.HttpResponse("Forbidden", status_code=403)
    
    req_body = req.get_json()
    email = req_body['email']
    password_hash = bcrypt.hashpw(req_body['password'].encode('utf-8'), bcrypt.gensalt())
    
    connection = get_db_connection()
    cursor = connection.cursor()
    query = "INSERT INTO users (email, password, role, admin_id) VALUES (%s, %s, %s, %s)"
    cursor.execute(query, (email, password_hash, 'doctor', admin_id))
    connection.commit()
    doctor_id = cursor.lastrowid
    connection.close()
    return func.HttpResponse(str(doctor_id), status_code=200)

# New: Verify/Deny Booking (Doctor only)
@app.route(route="verify_booking")
def verify_booking(req: func.HttpRequest) -> func.HttpResponse:
    user = validate_jwt(req)
    role, admin_id = get_user_role_and_admin(user['username'])
    if role != 'doctor':
        return func.HttpResponse("Forbidden", status_code=403)
    
    req_body = req.get_json()
    bid = req_body['bid']
    action = req_body['action']  # 'verify' or 'deny'
    
    connection = get_db_connection()
    cursor = connection.cursor()
    check_query = "SELECT hospital_id FROM pbooking WHERE id=%s"
    cursor.execute(check_query, (bid,))
    hosp = cursor.fetchone()[0]
    if hosp != admin_id:
        return func.HttpResponse("Forbidden", status_code=403)
    
    status = 'verified' if action == 'verify' else 'denied'
    query = "UPDATE pbooking SET status=%s, verifier_doctor_id=%s WHERE id=%s"
    cursor.execute(query, (status, user['id'], bid))
    connection.commit()
    connection.close()
    return func.HttpResponse("Booking updated", status_code=200)

# New: Poll for AI Report
@app.route(route="poll_aireport")
def poll_aireport(req: func.HttpRequest) -> func.HttpResponse:
    user = validate_jwt(req)
    bid = req.params.get('bid')
    mrn = req.params.get('mrn')
    
    max_attempts = 10
    for attempt in range(max_attempts):
        if download_aireport(bid=bid, mrn=mrn, download_path="/tmp/aireport.pdf"):
            with open("/tmp/aireport.pdf", "rb") as pdf_file:
                upload_pdf(blob_name=bid + ".pdf", data=pdf_file)
            connection = get_db_connection()
            query = "UPDATE pbooking SET aireport=1, status='completed' WHERE id=%s"
            cursor = connection.cursor()
            cursor.execute(query, (bid,))
            connection.commit()
            connection.close()
            return func.HttpResponse("AI Report fetched and uploaded", status_code=200)
        time.sleep(30)
    send_email("AI Report Pending", "AI report not ready; check Remidio manually.", user['username'])
    return func.HttpResponse("AI Report not ready after polling; emailed fallback", status_code=202)

# New: Internal Chat - Send Message
@app.route(route="send_message")
def send_message(req: func.HttpRequest) -> func.HttpResponse:
    user = validate_jwt(req)
    _, admin_id = get_user_role_and_admin(user['username'])
    
    req_body = req.get_json()
    to_user_id = req_body['to_user_id']
    message = req_body['message']
    
    connection = get_db_connection()
    cursor = connection.cursor()
    check_query = "SELECT admin_id FROM users WHERE id=%s"
    cursor.execute(check_query, (to_user_id,))
    to_admin = cursor.fetchone()[0]
    if to_admin != admin_id:
        connection.close()
        return func.HttpResponse("Cannot chat outside environment", status_code=403)
    
    query = "INSERT INTO chats (from_user_id, to_user_id, message) VALUES (%s, %s, %s)"
    cursor.execute(query, (user['id'], to_user_id, message))
    connection.commit()
    connection.close()
    return func.HttpResponse("Message sent", status_code=200)

# New: Internal Chat - Get Messages
@app.route(route="get_messages")
def get_messages(req: func.HttpRequest) -> func.HttpResponse:
    user = validate_jwt(req)
    to_user_id = req.params.get('to_user_id')
    
    connection = get_db_connection()
    cursor = connection.cursor()
    query = """
        SELECT from_user_id, message, timestamp, read 
        FROM chats 
        WHERE (from_user_id=%s AND to_user_id=%s) OR (from_user_id=%s AND to_user_id=%s)
        ORDER BY timestamp ASC
    """
    cursor.execute(query, (user['id'], to_user_id, to_user_id, user['id']))
    results = cursor.fetchall()
    messages = [{"from": r[0], "message": r[1], "time": str(r[2]), "read": r[3]} for r in results]
    
    update_query = "UPDATE chats SET read=1 WHERE to_user_id=%s AND from_user_id=%s"
    cursor.execute(update_query, (user['id'], to_user_id))
    connection.commit()
    connection.close()
    
    return func.HttpResponse(json.dumps(messages), status_code=200, mimetype="application/json")

# New: View External Patient Report
@app.route(route="view_external_report")
def view_external_report(req: func.HttpRequest) -> func.HttpResponse:
    user = validate_jwt(req)
    role, _ = get_user_role_and_admin(user['username'])
    if role not in ['admin', 'doctor']:
        return func.HttpResponse("Forbidden", status_code=403)
    
    bid = req.params.get('bid')
    connection = get_db_connection()
    cursor = connection.cursor()
    query = "SELECT status, hospital_id FROM pbooking WHERE id=%s"
    cursor.execute(query, (bid,))
    result = cursor.fetchone()
    status, hosp = result[0], result[1]
    if status != 'completed':
        connection.close()
        return func.HttpResponse("Report not completed", status_code=403)
    if hosp != user['admin_id'] and role != 'superadmin':
        connection.close()
        return func.HttpResponse("Forbidden", status_code=403)
    
    # Fetch report data (PDF path, images, diagnosis, comment)
    report = {
        "pdf": f"{bid}.pdf",
        "images": fetchimgs(bid),
        "diagnosis": result[2] if 'diagnosis' in result else None,  # Adjust based on query
        "comment": result[3] if 'specialist_comment' in result else None
    }
    connection.close()
    return func.HttpResponse(json.dumps(report), status_code=200, mimetype="application/json")

# New: Add Specialist Comment/Diagnosis
@app.route(route="add_comment")
def add_comment(req: func.HttpRequest) -> func.HttpResponse:
    user = validate_jwt(req)
    role, admin_id = get_user_role_and_admin(user['username'])
    if role != 'specialist':
        return func.HttpResponse("Forbidden", status_code=403)
    
    req_body = req.get_json()
    bid = req_body['bid']
    diagnosis = req_body['diagnosis']  # e.g., 'normal', 'mild_DR'
    comment = req_body['comment']  # Optional text
    
    connection = get_db_connection()
    cursor = connection.cursor()
    check_query = "SELECT hospital_id FROM pbooking WHERE id=%s"
    cursor.execute(check_query, (bid,))
    hosp = cursor.fetchone()[0]
    if hosp != admin_id:
        connection.close()
        return func.HttpResponse("Forbidden", status_code=403)
    
    query = "UPDATE pbooking SET diagnosis=%s, specialist_comment=%s WHERE id=%s"
    cursor.execute(query, (diagnosis, comment, bid))
    connection.commit()
    connection.close()
    return func.HttpResponse("Comment added", status_code=200)

# New: Get Stats for Admin (Diagnosis counts)
@app.route(route="get_stats")
def get_stats(req: func.HttpRequest) -> func.HttpResponse:
    user = validate_jwt(req)
    role, admin_id = get_user_role_and_admin(user['username'])
    if role not in ['admin', 'superadmin']:
        return func.HttpResponse("Forbidden", status_code=403)
    
    connection = get_db_connection()
    cursor = connection.cursor()
    if role == 'superadmin':
        query = "SELECT diagnosis, COUNT(*) as count FROM pbooking GROUP BY diagnosis"
    else:
        query = "SELECT diagnosis, COUNT(*) as count FROM pbooking WHERE hospital_id=%s GROUP BY diagnosis"
        cursor.execute(query, (admin_id,))
    cursor.execute(query)
    results = cursor.fetchall()
    stats = {r[0]: r[1] for r in results if r[0]}
    connection.close()
    return func.HttpResponse(json.dumps(stats), status_code=200, mimetype="application/json")

@app.route(route="get_patient")
def get_patient(req: func.HttpRequest) -> func.HttpResponse:
    user = validate_jwt(req)
    role, admin_id = get_user_role_and_admin(user['username'])
    mrn = req.params.get('mrn')
    connection = get_db_connection()
    if connection.is_connected():
        cursor = connection.cursor()
        if role == 'superadmin':
            query = "SELECT mrn, firstname, lastname, gender, dob, phone, email FROM patient WHERE mrn = %s"
            cursor.execute(query, (mrn,))
        else:
            query = "SELECT mrn, firstname, lastname, gender, dob, phone, email FROM patient WHERE mrn = %s AND hospital_id = %s"
            cursor.execute(query, (mrn, admin_id))
        result = cursor.fetchone()
        connection.close()
        if result:
            date_obj = datetime.strptime(str(result[4]), "%Y-%m-%d")
            date_str = date_obj.strftime("%B %d, %Y")
            patient = {
                "mrn": result[0],
                "name": f"{result[1]} {result[2]}",
                "gender": result[3],
                "dob": date_str,
                "phone": result[5],
                "email": result[6]
            }
            return func.HttpResponse(json.dumps(patient), status_code=200, mimetype="application/json")
        return func.HttpResponse("Patient not found", status_code=404)
    return func.HttpResponse("Failed to connect DB", status_code=500)