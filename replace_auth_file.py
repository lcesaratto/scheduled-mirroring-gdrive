import os
from pydrive import auth
import shutil


if __name__ == "__main__":
    path = os.path.abspath(auth.__file__)
    shutil.copy("./auth.py",path)