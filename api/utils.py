import requests
from openpyxl import Workbook


UPLOAD_FILE_URL = "https://tmpfiles.org/api/v1/upload"

def upload_file_to_cloud(file_path:str) -> str:
    myfiles = {'file': open(file_path ,'rb')}
    r = requests.post(UPLOAD_FILE_URL, files = myfiles)
    if r.status_code != 200:
        raise RuntimeError(r.text)

    r_url = r.json()['data']['url']
    # TODO: add /dl/
    return r_url

def generate_excel(save_file_path:str) -> None:
    wb = Workbook()

    # grab the active worksheet
    ws = wb.active

    # Data can be assigned directly to cells
    ws['A1'] = 42

    # Rows can also be appended
    ws.append([1, 2, 3])

    # Python types will automatically be converted
    import datetime
    ws['A2'] = datetime.datetime.now()

    # Save the file
    wb.save(save_file_path)