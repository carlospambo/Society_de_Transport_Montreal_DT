
import os

def resource_file_path(filename):
    pythonpath = os.environ.get("PYTHONPATH")
    directories = ['.'] if pythonpath is None else pythonpath.split(os.pathsep) + ['.']

    for d in directories:
        filepath = os.path.join(d, filename)
        if os.path.exists(filepath):
            return filepath

    print(f"File not found: {filename}")
    print("Tried the following directories:")
    print(directories)

    raise ValueError(f"File not found: {filename}")
