from pathlib import Path
from typing import Optional, List

from pydrive.auth import GoogleAuth
from pydrive.drive import GoogleDrive


class DriveHandler:
    def __init__(self):
        self.gauth = GoogleAuth()
        self.drive = GoogleDrive(self.gauth)

    def get_list(self, parent_id: str):
        return self.drive.ListFile({
            'q': f"'{parent_id}' in parents and trashed=false"
        }).GetList()

    def search_file(self, file_name: str, parent_id: str) -> Optional[str]:
        file_list = self.get_list(parent_id)

        for file in file_list:
            if file['title'] == f"{file_name}.mp3":
                return file['id']

        return None

    def upload_file(self, file_path: Path, parent_id: str):
        print(f"Uploading {file_path.name}")
        self.delete_file(file_path.name, parent_id)

        file = self.drive.CreateFile({
            'parents': [{
                'kind': 'drive#childList',
                'id': parent_id
            }],
            'title': str(file_path.name)
        })
        file.SetContentFile(str(file_path.absolute()))
        file.Upload()

    def copy_dir(self, directory: Path, parent_id: str):
        file_paths: List[Path] = []
        for file in directory.iterdir():
            if file.is_file():
                file_paths.append(file)

        for file in file_paths:
            self.upload_file(file, parent_id)

    def delete_file(self, file_name: str, parent_id: str) -> bool:
        search_result = self.search_file(file_name, parent_id)

        if search_result is not None:
            file_to_be_deleted = self.drive.CreateFile({
                'id': search_result
            })

            file_to_be_deleted.Trash()

        return bool(search_result)
