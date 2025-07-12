import os
import subprocess
from urllib.parse import urlparse

class Git:
    def __init__(self, url):
        self.url = url
        self.username = self._get_username_from_url()
        self.repo_name = self._get_repo_name_from_url()

    def _get_username_from_url(self):
        path = urlparse(self.url).path
        parts = path.strip('/').split('/')
        if len(parts) >= 2:
            return parts[-2]
        return None

    def _get_repo_name_from_url(self):
        path = urlparse(self.url).path
        repo_name = os.path.splitext(os.path.basename(path))[0]
        return repo_name

    def verify_access(self):
        """Verifies access to the git repository."""
        try:
            subprocess.run(['git', 'ls-remote', self.url], check=True, capture_output=True)
            return True
        except subprocess.CalledProcessError:
            return False

    def is_cloned(self, path="repos"):
        """Checks if the repository is already cloned, and if so, pulls the latest changes."""
        if not self.username:
            clone_dir = path
        else:
            clone_dir = os.path.join(path, self.username)
        repo_path = os.path.join(clone_dir, self.repo_name)

        if os.path.isdir(repo_path):
            print(f"Repository '{self.repo_name}' already exists. Pulling latest changes...")
            try:
                subprocess.run(
                    ['git', 'pull'],
                    check=True,
                    cwd=repo_path,
                    capture_output=True,
                    text=True
                )
                print("Successfully pulled latest changes.")
            except subprocess.CalledProcessError as e:
                print(f"Error pulling latest changes: {e.stderr}")
            return True
        return False

    def clone(self, path="repos"):
        """Clones the repository into the specified path."""
        if not self.username:
            clone_dir = path
        else:
            clone_dir = os.path.join(path, self.username)

        repo_dir = os.path.join(clone_dir, self.repo_name)

        if not os.path.isdir(repo_dir):
            try:
                os.makedirs(clone_dir, exist_ok=True)
                subprocess.run(['git', 'clone', self.url], check=True, cwd=clone_dir)
                return True
            except subprocess.CalledProcessError as e:
                print(f"Error cloning repository: {e.stderr.decode()}")
                return False
        else:
            print(f"Repository '{self.repo_name}' already cloned.")
            return False

    def get_codebase(self, path="repos"):
        """Returns the entire codebase as a hashmap, filtered by code extensions."""
        if not self.username:
            clone_dir = path
        else:
            clone_dir = os.path.join(path, self.username)
        repo_path = os.path.join(clone_dir, self.repo_name)

        codebase = {}
        code_extensions = [
            '.py', '.dart', '.c', '.cpp', '.h', '.hpp', '.java', '.js', '.ts',
            '.jsx', '.tsx', '.go', '.rs', '.swift', '.kt', '.kts', '.cs', '.php',
            '.rb', '.html', '.css', '.scss', '.less', '.sh', '.zsh', '.fish',
            '.bash', '.json', '.xml', '.yaml', '.yml', '.md'
        ]
        for root, _, files in os.walk(repo_path):
            if '.git' in root.split(os.path.sep):
                continue
            for file in files:
                if any(file.endswith(ext) for ext in code_extensions):
                    file_path = os.path.join(root, file)
                    try:
                        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                            codebase[os.path.relpath(file_path, repo_path)] = f.read()
                    except Exception as e:
                        print(f"Error reading file {file_path}: {e}")
        return codebase
