from pathlib import Path
from pydrive.auth import GoogleAuth
from pydrive.drive import GoogleDrive


def upload_file(file_path: Path, id: str):
    gauth = GoogleAuth()
    drive = GoogleDrive(gauth)
    file = drive.CreateFile({
        'parents': [{
            'kind': 'drive#childList',
            'id': id
        }]
    })
    file.SetContentFile(str(file_path.absolute()))
    file.Upload()