from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
import os
import pickle

SCOPES = ['https://www.googleapis.com/auth/drive.file']
CLIENT_SECRET_FILE = 'credentials.json'

def main():
    creds = None
    if os.path.exists('token.pickle'):
        os.remove('token.pickle')  # 删除现有令牌文件
    if os.path.exists(CLIENT_SECRET_FILE):
        flow = InstalledAppFlow.from_client_secrets_file(CLIENT_SECRET_FILE, SCOPES)
        creds = flow.run_local_server(port=8501)  # 指定固定端口
        with open('token.pickle', 'wb') as token:
            pickle.dump(creds, token)
    print("Token saved to token.pickle")

if __name__ == '__main__':
    main()
