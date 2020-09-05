# Import Google libraries
from pydrive.auth import GoogleAuth
from pydrive.drive import GoogleDrive
from pydrive.files import GoogleDriveFileList
import googleapiclient.errors

# Import general libraries
from os import chdir, listdir, stat, walk, path, sep, system
from sys import exit
import ast
import time
from pprint import pprint
from datetime import date, datetime


class Sync(object):
    def __init__(self, days=[], local_folders=[], parent_folder=""):
        self.drive = self._authenticate()
        self.days = days
        self.local_folders = self._load_local_folders(local_folders)
        self.drive_parent_folder = parent_folder
        self.today, self.folders_id = self._create_base_dict()

    def _authenticate(self):
        gauth = GoogleAuth()
        return GoogleDrive(gauth)

    def _load_local_folders(self, local_folders):
        return [path.normpath(local_folder) for local_folder in local_folders]

    def _create_base_dict(self):
        folders_id = {}
        folders_id[self.drive_parent_folder] = {}
        folders_id[self.drive_parent_folder]["id"] = self._get_folder_id(folder=self.drive_parent_folder)
        folders_id[self.drive_parent_folder]["days"] = {}
        
        for day in self.days:
            folders_id[self.drive_parent_folder]["days"][day] = {}
            folders_id[self.drive_parent_folder]["days"][day]["id"] = None
            folders_id[self.drive_parent_folder]["days"][day]["principal_folders"] = {}

        all_days={0:"lunes", 1:"martes", 2:"miercoles", 3:"jueves", 4:"viernes", 5:"sabado", 6:"domingo"}
        today = all_days[date.today().weekday()]

        for local_folder in self.local_folders:
            folders_id[self.drive_parent_folder]["days"][today]["principal_folders"][local_folder] = {}
            folders_id[self.drive_parent_folder]["days"][today]["principal_folders"][local_folder]["id"] = None
            folders_id[self.drive_parent_folder]["days"][today]["principal_folders"][local_folder]["subfolders"] = {}
            folders_id[self.drive_parent_folder]["days"][today]["principal_folders"][local_folder]["files"] = {}
        return today, folders_id

    def _create_empty_folders(self):
        # Create current day folder if not already created
        self.folders_id[self.drive_parent_folder]["days"][self.today]["id"] = self._create_folder(folder_name=self.today,
                                                                                                parent_dict=self.folders_id[self.drive_parent_folder])

        # Create all local folders to clone in the cloud
        for local_folder in self.local_folders:
            self.folders_id[self.drive_parent_folder]["days"][self.today]["principal_folders"][local_folder]["id"] = self._create_folder(folder_name=local_folder,
                                                                                                                                    parent_dict=self.folders_id[self.drive_parent_folder]["days"][self.today])
            # Clone all subfolders
            for dir in walk(local_folder):
            # dir: [path, folders, files]
                for subfolder in dir[1]:
                    if path.relpath(path.abspath(dir[0]), local_folder) == '.':
                        rel_subfolder_key = subfolder
                        self.folders_id[self.drive_parent_folder]["days"][self.today]["principal_folders"][local_folder]["subfolders"][rel_subfolder_key] = {}
                        self.folders_id[self.drive_parent_folder]["days"][self.today]["principal_folders"][local_folder]["subfolders"][rel_subfolder_key]["id"] = self._create_folder(folder_name=subfolder,
                                                                                                                                                                                parent_dict=self.folders_id[self.drive_parent_folder]["days"][self.today]["principal_folders"][local_folder])
                    else:
                        rel_parent_key = path.relpath(path.abspath(dir[0]), local_folder)
                        rel_subfolder_key = '\\'.join([rel_parent_key, subfolder])
                        self.folders_id[self.drive_parent_folder]["days"][self.today]["principal_folders"][local_folder]["subfolders"][rel_subfolder_key] = {}
                        self.folders_id[self.drive_parent_folder]["days"][self.today]["principal_folders"][local_folder]["subfolders"][rel_subfolder_key]["id"] = self._create_folder(folder_name=subfolder,
                                                                                                                                                                                parent_dict=self.folders_id[self.drive_parent_folder]["days"][self.today]["principal_folders"][local_folder]["subfolders"][rel_parent_key])
                    
                    self.folders_id[self.drive_parent_folder]["days"][self.today]["principal_folders"][local_folder]["subfolders"][rel_subfolder_key]["files"] = {}
                
    def _get_folder_id(self, parent_folder_id="root", folder=""):
        # Auto-iterate through all files in the parent folder.
        file_list = GoogleDriveFileList()
        try:
            file_list = self.drive.ListFile(
                {'q': "'{0}' in parents and trashed=false".format(
                    parent_folder_id)}
            ).GetList()
        # Exit if the parent folder doesn't exist
        except googleapiclient.errors.HttpError as err:
            # Parse error message
            message = ast.literal_eval(err.content)['error']['message']
            if message == 'File not found: ':
                print(message + folder)
                exit(1)
                # Exit with stacktrace in case of other error
            else:
                raise

        # Find the the destination folder in the parent folder's files
        for file1 in file_list:
            # print(file1['title'])
            if file1['title'] == folder:
                # print('title: %s, id: %s' % (file1['title'], file1['id']))
                return file1['id']

    def _get_files_id(self, parent_folder_id="root"):
        # Auto-iterate through all files in the parent folder.
        file_list = GoogleDriveFileList()
        try:
            file_list = self.drive.ListFile(
                {'q': "'{0}' in parents and trashed=false".format(
                    parent_folder_id)}
            ).GetList()
        # Exit if the parent folder doesn't exist
        except googleapiclient.errors.HttpError as err:
            # Parse error message
            message = ast.literal_eval(err.content)['error']['message']
            if message == 'File not found: ':
                exit(1)
                # Exit with stacktrace in case of other error
            else:
                raise

        # Find the the destination folder in the parent folder's files
        found_files = {}
        for filename in file_list:
            if filename['mimeType'] != 'application/vnd.google-apps.folder':
                found_files[filename['title']] = filename['id']

        return found_files

    def _create_folder(self, folder_name, parent_dict):

        folder_id = self._get_folder_id(parent_folder_id=parent_dict["id"], folder=folder_name)

        if not folder_id:
            folder_metadata ={
                            'title': folder_name,
                            'mimeType': 'application/vnd.google-apps.folder',  # Define the file type as folder
                            'parents': [{"kind": "drive#fileLink", "id": parent_dict["id"]}] # ID of the parent folder
                            }
            folder = self.drive.CreateFile(folder_metadata)
            folder.Upload()
            return folder['id']
        else:
            return folder_id

    def _check_current_files(self):
        for principal_folder, principal_folder_json in self.folders_id[self.drive_parent_folder]["days"][self.today]["principal_folders"].items():
            self.folders_id[self.drive_parent_folder]["days"][self.today]["principal_folders"][principal_folder]["files"] = self._get_files_id(parent_folder_id=principal_folder_json["id"])

            for subfolder, subfolder_json in principal_folder_json["subfolders"].items():
                self.folders_id[self.drive_parent_folder]["days"][self.today]["principal_folders"][principal_folder]["subfolders"][subfolder]["files"] = self._get_files_id(parent_folder_id=subfolder_json["id"])

    def _copy_content(self):
        for principal_folder, principal_folder_json in self.folders_id[self.drive_parent_folder]["days"][self.today]["principal_folders"].items():
            for filename in listdir(principal_folder): # List everything in current directory
                if path.isfile(path.abspath('\\'.join([principal_folder, filename]))): # Chech if it is not a folder
                    full_local_file_path = path.abspath('\\'.join([principal_folder, filename]))
                    if filename in principal_folder_json["files"].keys(): # If the file is already in the cloud
                        if (datetime.today()-datetime.fromtimestamp(path.getmtime(full_local_file_path))).days < 8:
                            self._update_files(file_id=principal_folder_json["files"][filename], full_local_file_path=full_local_file_path)
                    else:
                        self._upload_files(principal_folder_json["id"], full_local_file_path)

            for subfolder, subfolder_json in principal_folder_json["subfolders"].items():
                for filename in listdir(path.abspath('\\'.join([principal_folder, subfolder]))):
                    if path.isfile(path.abspath('\\'.join([principal_folder, subfolder, filename]))):
                        full_local_file_path = path.abspath('\\'.join([principal_folder, subfolder, filename]))
                        if filename in subfolder_json["files"].keys(): # If the file is already in the cloud
                            if (datetime.today()-datetime.fromtimestamp(path.getmtime(full_local_file_path))).days < 8:
                                self._update_files(file_id=subfolder_json["files"][filename], full_local_file_path=full_local_file_path)
                        else:
                            self._upload_files(subfolder_json["id"], full_local_file_path)

    def _upload_files(self, folder_id, full_local_file_path):
        # Check the file's size
        if stat(full_local_file_path).st_size > 0:
            # Upload file to folder.
            f = self.drive.CreateFile(
                {
                    "title": full_local_file_path.split(sep)[-1],
                    "parents":
                    [{
                        "kind": "drive#fileLink",
                        "id": folder_id
                    }]
                })
            f.SetContentFile(full_local_file_path)
            f.Upload()

    def _update_files(self, file_id, full_local_file_path):
        # Check the file's size
        if stat(full_local_file_path).st_size > 0:
            f = self.drive.CreateFile({'id': file_id})
            f.SetContentFile(full_local_file_path)
            f.Upload()

    def syncronize(self):
        self._create_empty_folders()
        self._check_current_files()
        self._copy_content()

        pprint(self.folders_id)
        print('Sync complete !')

def main():
    with open('./data_to_config/days_to_backup.txt') as file:
        days = [line.rstrip('\n') for line in file]

    with open('./data_to_config/local_folders_path.txt') as file:
        local_folders = [line.rstrip('\n') for line in file]
    
    SyncObj = Sync(days=days, local_folders=local_folders, parent_folder=open('./data_to_config/drive_parent_folder.txt').read())
    SyncObj.syncronize()

    # Shut down computer
    # system("shutdown /s /t 1")


if __name__ == "__main__":
    main()
