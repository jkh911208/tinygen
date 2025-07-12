import os
import subprocess
from urllib.parse import urlparse

class Git:
    def __init__(self, url):
        self.url = url
        self.username = self._get_username_from_url()
        self.repo_name = self._get_repo_name_from_url()
        self._found_repo_path = None

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

    def _find_repo_path(self, base_path):
        """
        Recursively searches for a git repository with a matching remote URL.
        Returns the path to the repository if found, otherwise None.
        """
        if self._found_repo_path and os.path.isdir(self._found_repo_path):
            return self._found_repo_path

        if not os.path.isdir(base_path):
            return None

        for root, dirs, _ in os.walk(base_path):
            if '.git' in dirs:
                repo_path_candidate = root
                dirs[:] = []
                try:
                    remote_url = subprocess.check_output(
                        ['git', 'config', '--get', 'remote.origin.url'],
                        cwd=repo_path_candidate,
                        text=True,
                        stderr=subprocess.DEVNULL
                    ).strip()
                    if remote_url == self.url:
                        self._found_repo_path = repo_path_candidate
                        return repo_path_candidate
                except subprocess.CalledProcessError:
                    continue
        return None

    def verify_access(self):
        """Verifies access to the git repository."""
        try:
            subprocess.run(['git', 'ls-remote', self.url], check=True, capture_output=True)
            return True
        except subprocess.CalledProcessError:
            return False

    def is_cloned(self, base_path="repos"):
        """Checks if the repository is already cloned, and if so, pulls the latest changes."""
        repo_path = self._find_repo_path(base_path)

        if repo_path:
            print(f"Repository '{self.repo_name}' already exists at '{repo_path}'. Pulling latest changes...")
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

    def clone(self, base_path="repos"):
        """Clones the repository into the specified path."""
        if self._find_repo_path(base_path):
            print(f"Repository '{self.repo_name}' already cloned.")
            return False

        if not self.username:
            clone_dir = base_path
        else:
            clone_dir = os.path.join(base_path, self.username)

        repo_dir = os.path.join(clone_dir, self.repo_name)

        if os.path.isdir(repo_dir):
            print(f"Directory '{repo_dir}' already exists but is not the correct repository. Cloning skipped.")
            return False

        try:
            os.makedirs(clone_dir, exist_ok=True)
            subprocess.run(['git', 'clone', self.url], check=True, cwd=clone_dir)
            self._found_repo_path = repo_dir
            return True
        except subprocess.CalledProcessError as e:
            print(f"Error cloning repository: {e.stderr.decode()}")
            return False

    def get_codebase(self, base_path="repos"):
        """Returns the entire codebase as a hashmap, filtered by code extensions."""
        repo_path = self._find_repo_path(base_path)
        if not repo_path:
            print(f"Repository for URL '{self.url}' not found in '{base_path}'.")
            return {}

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