import os

def delete_file(file_path: str) -> bool:
    try:
        if os.path.isfile(file_path):
            os.remove(file_path)
            return True
        return False
    except Exception as e:
        print(f"Error deleting file {file_path}: {e}")
        return False