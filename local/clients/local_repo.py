"""Local repository handler."""
from typing import List, Optional
from pathlib import Path


class LocalRepoClient:
    """Client for accessing local repository."""
    
    def __init__(self, repo_path: str):
        """Initialize local repo client.
        
        Args:
            repo_path: Path to local repository
        """
        self.repo_path = Path(repo_path)
        if not self.repo_path.exists():
            raise FileNotFoundError(f"Repository path not found: {repo_path}")
        if not self.repo_path.is_dir():
            raise ValueError(f"Repository path is not a directory: {repo_path}")
    
    def get_repo_path(self) -> str:
        """Get absolute repository path.
        
        Returns:
            Absolute path to repository
        """
        return str(self.repo_path.absolute())
    
    def list_files(self, extensions: Optional[List[str]] = None) -> List[str]:
        """List files in repository.
        
        Args:
            extensions: List of file extensions to filter (e.g., ['.py', '.js'])
            
        Returns:
            List of relative file paths
        """
        files = []
        
        for file_path in self.repo_path.rglob('*'):
            if file_path.is_file():
                # Skip common ignore patterns
                if any(ignore in file_path.parts for ignore in ['.git', '__pycache__', 'node_modules', '.venv', 'venv']):
                    continue
                    
                if extensions is None or file_path.suffix in extensions:
                    files.append(str(file_path.relative_to(self.repo_path)))
        
        return sorted(files)
    
    def get_file_content(self, relative_path: str) -> str:
        """Get content of a file.
        
        Args:
            relative_path: Relative path to file
            
        Returns:
            File content as string
        """
        file_path = self.repo_path / relative_path
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {relative_path}")
        
        return file_path.read_text(encoding='utf-8')
    
    def file_exists(self, relative_path: str) -> bool:
        """Check if file exists in repository.
        
        Args:
            relative_path: Relative path to file
            
        Returns:
            True if file exists
        """
        return (self.repo_path / relative_path).exists()