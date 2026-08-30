import sys
import os
import subprocess

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python push_to_github.py <GITHUB_REPO_URL>")
        print("Example: python push_to_github.py https://github.com/username/NeoGuardian.git")
        sys.exit(1)

    repo_url = sys.argv[1].strip()
    current_dir = os.path.dirname(os.path.abspath(__file__))
    git_exe = os.path.join(current_dir, ".tools", "git", "cmd", "git.exe")

    if not os.path.exists(git_exe):
        git_exe = "git"

    print(f"[Git] Configuring remote origin: {repo_url}")
    subprocess.run([git_exe, "remote", "remove", "origin"], stderr=subprocess.DEVNULL)
    subprocess.run([git_exe, "remote", "add", "origin", repo_url], check=True)
    subprocess.run([git_exe, "branch", "-M", "main"], check=True)
    
    print("[Git] Pushing main branch to GitHub...")
    res = subprocess.run([git_exe, "push", "-u", "origin", "main"])
    if res.returncode == 0:
        print("\n[SUCCESS] Repository successfully pushed to GitHub!")
    else:
        print("\n[ERROR] Push failed. Please verify repository URL and your GitHub permissions.")
