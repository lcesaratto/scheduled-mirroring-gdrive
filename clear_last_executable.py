from os import system


if __name__ == "__main__":
    system("rmdir /s /q __pycache__")
    system("rmdir /s /q dist")
    system("rmdir /s /q build")
    system("del backup.spec")