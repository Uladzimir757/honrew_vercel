# Файл: build.py
import subprocess
import shutil
import sys
from pathlib import Path

DIST_DIR = Path("dist")
SOURCE_DIRS = ["app"] 
SRC_DIR = Path("src")
REQUIREMENTS_FILE = "py-requirements.txt"

def main():
    print("--- Starting FLATTENED build process ---")
    
    if DIST_DIR.exists():
        shutil.rmtree(DIST_DIR)
    DIST_DIR.mkdir()

    if SRC_DIR.exists():
        print(f"Copying contents of '{SRC_DIR}' to '{DIST_DIR}'...")
        shutil.copytree(SRC_DIR, DIST_DIR, dirs_exist_ok=True)
    else:
        print(f"FATAL ERROR: Source directory '{SRC_DIR}' not found!")
        exit(1)

    for dir_name in SOURCE_DIRS:
        source_path = Path(dir_name)
        if source_path.exists():
            print(f"Copying '{source_path}' to '{DIST_DIR / dir_name}'...")
            shutil.copytree(source_path, DIST_DIR / dir_name)
        else:
            print(f"FATAL ERROR: Source directory '{source_path}' not found!")
            exit(1)

    req_file_path = Path(REQUIREMENTS_FILE)
    if req_file_path.exists():
        print(f"Installing dependencies from '{REQUIREMENTS_FILE}' into '{DIST_DIR}'...")
        try:
            # === ФИНАЛЬНОЕ ИЗМЕНЕНИЕ ===
            # Удаляем флаг --python-version, чтобы избежать ненужных
            # строгих проверок pip.
            command = [
                sys.executable,
                "-m",
                "pip",
                "install",
                "-r",
                str(req_file_path),
                "--target",
                str(DIST_DIR)
            ]
            
            subprocess.check_call(command)
        except subprocess.CalledProcessError as e:
            print("\n--- PIP INSTALL FAILED ---")
            print(f"Error while running command: {' '.join(command)}")
            print(e)
            exit(1)
    else:
        print(f"FATAL ERROR: '{REQUIREMENTS_FILE}' not found!")
        exit(1)

    print("--- Build process finished successfully ---")

if __name__ == "__main__":
    main()