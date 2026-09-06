import hashlib

def calculate_file_hash(file_path):

    hash_object = hashlib.sha256()

    with open(file_path, "rb") as file:

        while chunk := file.read(8192):
            hash_object.update(chunk)

    return hash_object.hexdigest()
