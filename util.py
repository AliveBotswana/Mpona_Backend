import os
import smtplib
import datetime
import traceback
from email import encoders
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from datetime import timedelta

import jwt
from azure.identity import DefaultAzureCredential
from azure.keyvault.secrets import SecretClient
from azure.storage.blob import BlobServiceClient
import secrets
import requests
import mysql.connector

# fetchimgs
def fetchimgs(bid):
    blob_service_client = BlobServiceClient(account_url="https://mponasa.blob.core.windows.net",
                                           credential=DefaultAzureCredential())
    container_client = blob_service_client.get_container_client(container="images")
    blob_list = container_client.list_blobs(name_starts_with=f"{bid}/")
    images = []
    for blob in blob_list:
        blob_client = blob_service_client.get_blob_client(container="images", blob=blob.name)
        blob_data = blob_client.download_blob().readall()
        images.append({"name": blob.name, "data": blob_data})
    return images

# download_pdf
def download_pdf(blob_name):
    blob_service_client = BlobServiceClient(account_url="https://mponasa.blob.core.windows.net",
                                           credential=DefaultAzureCredential())
    blob_client = blob_service_client.get_blob_client(container="aireports", blob=blob_name)
    with open("/tmp/aireport.pdf", "wb") as download_file:
        download_file.write(blob_client.download_blob().readall())

# download_aireport
def download_aireport(bid, mrn, download_path):
    try:
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
            pdfurl = response.json()["data"]["aiReport"]["path"]
            response = requests.get(pdfurl)
            if response.status_code == 200:
                with open(download_path, 'wb') as file:
                    file.write(response.content)
                return True
            else:
                return False
        else:
            return False
    except Exception as e:
        error_traceback = traceback.format_exc()
        print(error_traceback)
        return False

# download_medioimages
def download_medioimages(bid, mrn, download_path):
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
            for idx, imgurl in enumerate(response.json()["data"]["images"]["fopImages"]["STANDARD"]):
                response = requests.get(imgurl["path"])
                if response.status_code == 200:
                    with open(f"{download_path}{idx}.jpeg", 'wb') as file:
                        file.write(response.content)
                else:
                    traceback.print_exc()
                    return False
            return True
        except Exception as e:
            traceback.print_exc()
            return False
    else:
        return False

# upload_pdf
def upload_pdf(blob_name, data):
    blob_service_client = BlobServiceClient(account_url="https://mponasa.blob.core.windows.net",
                                           credential=DefaultAzureCredential())
    blob_client = blob_service_client.get_blob_client(container="aireports", blob=blob_name)
    blob_client.upload_blob(data, overwrite=True)

# upload_images
def upload_images(folder_path, bid):
    blob_service_client = BlobServiceClient(account_url="https://mponasa.blob.core.windows.net",
                                           credential=DefaultAzureCredential())
    container_client = blob_service_client.get_container_client(container="images")
    for root, _, files in os.walk(folder_path):
        for file in files:
            if file.lower().endswith(('.png', '.jpg', '.jpeg', '.gif', '.bmp', '.tiff', '.webp')):
                file_path = os.path.join(root, file)
                blob_name = f"{bid}/{os.path.relpath(file_path, folder_path)}"
                with open(file_path, "rb") as data:
                    container_client.upload_blob(name=blob_name, data=data, overwrite=True)
                    print(f"Uploaded: {file_path} to blob: {blob_name}")

# getsecret
def getsecret(name):
    key_vault_url = "https://mponasecrets.vault.azure.net/"
    credential = DefaultAzureCredential()
    secret_client = SecretClient(vault_url=key_vault_url, credential=credential)
    secret = secret_client.get_secret(name)
    return secret.value

# send_email
def send_email(subject, body, recipient):
    attachment_path = "/tmp/aireport.pdf"
    sender = "shahan@autonicals.org"
    msg = MIMEMultipart()
    msg["From"] = sender
    msg["To"] = recipient
    msg["Subject"] = subject
    msg.attach(MIMEText(body, "plain"))
    with open(attachment_path, "rb") as attachment:
        part = MIMEBase("application", "octet-stream")
        part.set_payload(attachment.read())
    encoders.encode_base64(part)
    part.add_header(
        "Content-Disposition",
        f"attachment; filename={os.path.basename(attachment_path)}",
    )
    msg.attach(part)
    with smtplib.SMTP("smtp.gmail.com", 587) as server:
        server.starttls()
        server.login(sender, getsecret("SMTP"))
        server.sendmail(sender, recipient, msg.as_string())

# generate_api_token
def generate_api_token():
    return secrets.token_hex(32)

# getjwt (updated to include id, role, admin_id)
def getjwt(username, user_id, role, admin_id):
    access_token = jwt.encode(
        {'username': username, 'id': user_id, 'role': role, 'admin_id': admin_id, 'exp': datetime.datetime.now() + timedelta(hours=1)},
        os.getenv("JWT_SECRET_KEY"),
        algorithm='HS256'
    )
    refresh_token = jwt.encode(
        {'username': username, 'exp': datetime.datetime.now() + timedelta(days=7)},
        os.getenv("JWT_SECRET_KEY"),
        algorithm='HS256'
    )
    api_token = generate_api_token()
    return {
        'access_token': access_token,
        'refreshToken': refresh_token,
        'api_token': api_token
    }

# get_db_connection
def get_db_connection():
    username = os.getenv('MYSQLUSER')
    password = os.getenv('MYSQLPASS')
    host = os.getenv('MYSQLHOST')
    try:
        return mysql.connector.connect(host=host, user=username, password=password, database=username)
    except mysql.connector.Error as err:
        raise Exception(f"DB Connection Error: {err}")

# validate_jwt
def validate_jwt(req):
    auth_header = req.headers.get('Authorization')
    if not auth_header or not auth_header.startswith('Bearer '):
        raise Exception("Unauthorized")
    token = auth_header.split(' ')[1]
    try:
        return jwt.decode(token, os.getenv("JWT_SECRET_KEY"), algorithms=['HS256'])
    except:
        raise Exception("Invalid token")

# get_user_role_and_admin
def get_user_role_and_admin(username):
    connection = get_db_connection()
    cursor = connection.cursor()
    query = "SELECT role, admin_id FROM users WHERE email = %s"
    cursor.execute(query, (username,))
    result = cursor.fetchone()
    connection.close()
    if result:
        return result[0], result[1]
    raise Exception("User not found")