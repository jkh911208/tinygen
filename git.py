import os
import asyncio
from urllib.parse import urlparse


class Git:
    def __init__(self, url):
        self.url = url
        self.username = self._get_username_from_url()
        self.repo_name = self._get_repo_name_from_url()
        self._found_repo_path = None

    def _get_username_from_url(self):
        path = urlparse(self.url).path
        parts = path.strip("/").split("/")
        if len(parts) >= 2:
            return parts[-2]
        return None

    def _get_repo_name_from_url(self):
        path = urlparse(self.url).path
        repo_name = os.path.splitext(os.path.basename(path))[0]
        return repo_name

    def _get_git_repo_candidates(self, base_path):
        """
        Scans the base_path for directories containing a .git folder.
        This is a blocking I/O operation.
        """
        if not os.path.isdir(base_path):
            print(
                f"DEBUG: Base path '{base_path}' does not exist or is not a directory."
            )
            return []
        candidates = []
        for root, dirs, _ in os.walk(base_path):
            if ".git" in dirs:
                candidates.append(root)
                dirs[:] = []  # Prune search deeper in this directory
        return candidates

    async def _find_repo_path(self, base_path):
        """
        Finds the path to a cloned repository matching self.url.
        It first gets a list of potential git repositories and then
        asynchronously checks their remote URL.
        """
        print(
            f"DEBUG: _find_repo_path called with base_path='{base_path}' for URL='{self.url}'"
        )
        if self._found_repo_path and os.path.isdir(self._found_repo_path):
            print(f"DEBUG: Using cached repo path: {self._found_repo_path}")
            return self._found_repo_path

        candidates = await asyncio.to_thread(self._get_git_repo_candidates, base_path)
        print(f"DEBUG: Found {len(candidates)} potential repo candidates: {candidates}")

        for repo_path_candidate in candidates:
            print(f"DEBUG: Checking candidate: {repo_path_candidate}")
            try:
                proc = await asyncio.create_subprocess_exec(
                    "git",
                    "config",
                    "--get",
                    "remote.origin.url",
                    cwd=repo_path_candidate,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.DEVNULL,
                )
                stdout, _ = await proc.communicate()

                if proc.returncode == 0:
                    remote_url = stdout.decode().strip()
                    print(
                        f"DEBUG: Candidate '{repo_path_candidate}' remote URL: '{remote_url}'"
                    )
                    normalized_remote_url = remote_url.removesuffix(".git")
                    normalized_self_url = self.url.removesuffix(".git")
                    if normalized_remote_url == normalized_self_url:
                        print(f"DEBUG: Match found! Repo path: {repo_path_candidate}")
                        self._found_repo_path = repo_path_candidate
                        return repo_path_candidate
                    else:
                        print(
                            f"DEBUG: No match. Expected '{self.url}', got '{remote_url}'"
                        )
                else:
                    print(
                        f"DEBUG: Failed to get remote URL for '{repo_path_candidate}'. Return code: {proc.returncode}"
                    )
            except Exception as e:
                print(f"DEBUG: Error checking candidate '{repo_path_candidate}': {e}")
                continue

        print(
            f"DEBUG: No matching repository found for URL='{self.url}' in '{base_path}'."
        )
        return None

    async def verify_access(self):
        print(f"DEBUG: Verifying access to {self.url}")
        proc = await asyncio.create_subprocess_exec(
            "git",
            "ls-remote",
            self.url,
            stdout=asyncio.subprocess.DEVNULL,
            stderr=asyncio.subprocess.DEVNULL,
        )
        await proc.wait()
        if proc.returncode == 0:
            print(f"DEBUG: Access verified for {self.url}")
        else:
            print(
                f"DEBUG: Access verification failed for {self.url}. Return code: {proc.returncode}"
            )
        return proc.returncode == 0

    async def is_cloned(self, base_path="repos"):
        print(f"DEBUG: Checking if cloned: URL='{self.url}', base_path='{base_path}'")
        repo_path = await self._find_repo_path(base_path)
        if repo_path:
            print(
                f"Repository '{self.repo_name}' already exists at '{repo_path}'. Pulling latest changes..."
            )
            proc = await asyncio.create_subprocess_exec(
                "git",
                "pull",
                cwd=repo_path,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            stdout, stderr = await proc.communicate()
            if proc.returncode == 0:
                print("Successfully pulled latest changes.")
            else:
                print(f"Error pulling latest changes: {stderr.decode()}")
            return True
        print(f"DEBUG: Repository '{self.repo_name}' not found in '{base_path}'.")
        return False

    async def clone(self, base_path="repos"):
        print(f"DEBUG: Attempting to clone: URL='{self.url}', base_path='{base_path}'")
        if await self._find_repo_path(base_path):
            print(f"Repository '{self.repo_name}' already cloned.")
            return False

        if not self.username:
            clone_dir = base_path
        else:
            clone_dir = os.path.join(base_path, self.username)

        repo_dir = os.path.join(clone_dir, self.repo_name)

        if os.path.isdir(repo_dir):
            print(
                f"Directory '{repo_dir}' already exists but is not the correct repository. Cloning skipped."
            )
            return False

        await asyncio.to_thread(os.makedirs, clone_dir, exist_ok=True)

        print(f"DEBUG: Cloning '{self.url}' into '{clone_dir}'")
        proc = await asyncio.create_subprocess_exec(
            "git",
            "clone",
            self.url,
            cwd=clone_dir,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, stderr = await proc.communicate()

        if proc.returncode == 0:
            print(f"DEBUG: Successfully cloned to {repo_dir}")
            self._found_repo_path = repo_dir
            return True
        else:
            print(f"Error cloning repository: {stderr.decode()}")
            return False

    def _get_codebase_filepaths_blocking(self, repo_path):
        filepaths = []
        code_extensions = [
            ".py",
            ".dart",
            ".c",
            ".cpp",
            ".h",
            ".hpp",
            ".java",
            ".js",
            ".ts",
            ".jsx",
            ".tsx",
            ".go",
            ".rs",
            ".swift",
            ".kt",
            ".kts",
            ".cs",
            ".php",
            ".rb",
            ".html",
            ".css",
            ".scss",
            ".less",
            ".sh",
            ".zsh",
            ".fish",
            ".bash",
            ".json",
            ".xml",
            ".yaml",
            ".yml",
            ".md",
        ]
        for root, _, files in os.walk(repo_path):
            if ".git" in root.split(os.path.sep):
                continue
            for file in files:
                if any(file.endswith(ext) for ext in code_extensions):
                    filepaths.append(os.path.join(root, file))
        return filepaths

    def _read_file_blocking(self, filepath):
        with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
            return f.read()

    async def _read_file_async(self, filepath):
        try:
            return await asyncio.to_thread(self._read_file_blocking, filepath)
        except Exception as e:
            print(f"Error reading file {filepath}: {e}")
            return None

    async def get_codebase(self, base_path="repos"):
        print(
            f"DEBUG: get_codebase called for URL='{self.url}', base_path='{base_path}'"
        )
        repo_path = await self._find_repo_path(base_path)
        if not repo_path:
            print(
                f"Repository for URL '{self.url}' not found in '{base_path}'. Cannot get codebase."
            )
            return {}

        filepaths = await asyncio.to_thread(
            self._get_codebase_filepaths_blocking, repo_path
        )
        print(f"DEBUG: Found {len(filepaths)} files in codebase for {repo_path}")

        tasks = [self._read_file_async(filepath) for filepath in filepaths]
        contents = await asyncio.gather(*tasks)

        codebase = {}
        for filepath, content in zip(filepaths, contents):
            if content is not None:
                relative_path = os.path.relpath(filepath, repo_path)
                codebase[relative_path] = content
        print(f"DEBUG: Codebase contains {len(codebase)} files.")
        return codebase
