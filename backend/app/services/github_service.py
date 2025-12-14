import os
import subprocess
from pathlib import Path
from datetime import datetime
from sqlalchemy.orm import Session
from app.models.notification_settings import NotificationHistory

class GithubService:
    def __init__(self):
        self.default_token = os.getenv("GITHUB_TOKEN")
        self.default_user = os.getenv("GITHUB_USER")

    def _build_auth_repo_url(self, repo_url: str, token: str, username: str) -> str:
        # Supports https URLs. For SSH, token won't work.
        if repo_url.startswith("https://"):
            # Insert token into URL: https://<username>:<token>@github.com/owner/repo.git
            without_protocol = repo_url[len("https://"):]
            # Ensure .git suffix for push endpoints
            if not without_protocol.endswith('.git'):
                without_protocol = without_protocol + '.git'
            return f"https://{username}:{token}@" + without_protocol
        return repo_url

    def push_to_repo(self, repo_url: str, local_path: str, commit_message: str,
                     token: str = None, username: str = None, db: Session = None, project_id: int = None, scan_id: int = None) -> dict:
        token = token or self.default_token
        username = username or self.default_user
        if not token or not username:
            return {"success": False, "error": "Missing GitHub token or username"}

        local_dir = Path(local_path)
        if local_dir.is_file():
            local_dir = local_dir.parent

        if not local_dir.exists():
            return {"success": False, "error": "Local path does not exist"}

        try:
            # Initialize git repo if needed
            if not (local_dir / ".git").exists():
                subprocess.run(["git", "init"], cwd=str(local_dir), check=True)

            # Set user
            subprocess.run(["git", "config", "user.name", username], cwd=str(local_dir), check=True)
            subprocess.run(["git", "config", "user.email", f"{username}@users.noreply.github.com"], cwd=str(local_dir), check=True)

            # Add remote (overwrite origin)
            auth_url = self._build_auth_repo_url(repo_url, token, username)
            subprocess.run(["git", "remote", "remove", "origin"], cwd=str(local_dir), check=False)
            subprocess.run(["git", "remote", "add", "origin", auth_url], cwd=str(local_dir), check=True)

            # Add all and commit
            subprocess.run(["git", "add", "."], cwd=str(local_dir), check=True)
            # Allow empty commit if nothing changed to avoid failure
            subprocess.run(["git", "commit", "-m", commit_message], cwd=str(local_dir), check=False)

            # Create default branch if not exists
            subprocess.run(["git", "branch", "-M", "main"], cwd=str(local_dir), check=False)

            # Fetch and attempt to rebase/pull to avoid non-fast-forward errors
            subprocess.run(["git", "fetch", "origin", "main"], cwd=str(local_dir), check=False)
            subprocess.run(["git", "pull", "--rebase", "origin", "main"], cwd=str(local_dir), check=False)

            # Push
            result = subprocess.run(["git", "push", "-u", "origin", "main"], cwd=str(local_dir), capture_output=True, text=True)
            if result.returncode != 0:
                # Log failure notification
                if db and project_id:
                    try:
                        db.add(NotificationHistory(
                            project_id=project_id,
                            scan_id=scan_id,
                            notification_type="push_failed",
                            subject=f"GitHub push failed",
                            recipients=[],
                            sent_at=datetime.utcnow(),
                            status="failed",
                        ))
                        db.commit()
                    except Exception:
                        pass
                return {"success": False, "error": result.stderr or "Failed to push"}

            # Log success notification
            if db and project_id:
                try:
                    db.add(NotificationHistory(
                        project_id=project_id,
                        scan_id=scan_id,
                        notification_type="push_success",
                        subject=f"GitHub push succeeded",
                        recipients=[],
                        sent_at=datetime.utcnow(),
                        status="sent",
                    ))
                    db.commit()
                except Exception:
                    pass
            return {"success": True}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def test_credentials(self, repo_url: str, token: str = None, username: str = None) -> dict:
        token = token or self.default_token
        username = username or self.default_user
        if not token or not username:
            return {"success": False, "error": "Missing GitHub token or username"}
        try:
            auth_url = self._build_auth_repo_url(repo_url, token, username)
            # ls-remote checks access rights without cloning
            result = subprocess.run(["git", "ls-remote", auth_url], capture_output=True, text=True)
            if result.returncode != 0:
                return {"success": False, "error": result.stderr or "Access denied"}
            return {"success": True}
        except Exception as e:
            return {"success": False, "error": str(e)}
