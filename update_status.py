import os
import re
import urllib.request
import json
import datetime

# Configuration
USERNAME = "Bestdoom20"
README_PATH = "README.md"

def fetch_github_data(url):
    req = urllib.request.Request(url)
    # Inject the automatic GitHub Token to authorize the request and bypass 403 blocks
    token = os.environ.get("GITHUB_TOKEN")
    if token:
        req.add_header('Authorization', f'token {token}')
    req.add_header('User-Agent', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)')
    
    with urllib.request.urlopen(req) as response:
        return json.loads(response.read().decode())

def main():
    try:
        # 1. Fetch User Profile Data
        user_data = fetch_github_data(f"https://api.github.com/users/{USERNAME}")
        
        created_at_str = user_data["created_at"].split("T")[0]
        created_year = int(created_at_str.split("-")[0])
        current_year = datetime.datetime.now().year
        years_active = max(1, current_year - created_year)
        
        public_repos = user_data.get("public_repos", 0)

        # 2. Fetch Repositories to Calculate Stars
        repos_data = fetch_github_data(f"https://api.github.com/users/{USERNAME}/repos?per_page=100")
        total_stars = sum(repo.get("stargazers_count", 0) for repo in repos_data)
        personal_projects = len(repos_data)

        # 3. Static Baseline Metrics
        total_commits = 31890
        total_issues = 792
        total_prs = 1784
        commit_streak = "2,697" 

        # 4. Construct the Real-Time Layout String
        new_stats_line = (
            f"I joined GitHub **{years_active}** {'years' if years_active > 1 else 'year'} ago and have since "
            f"pushed **{total_commits:,}** commits, opened **{total_issues:,}** issues, "
            f"submitted **{total_prs:,}** pull requests, and earned **{total_stars:,}** stars "
            f"across **{personal_projects}** personal projects, with contributions to **{public_repos}** public repositories.\n\n"
            f"I'm currently on a **{commit_streak}**-day commit streak."
        )

        # 5. Read and Regex Inject into Target Readme File
        with open(README_PATH, "r", encoding="utf-8") as f:
            content = f.read()

        pattern = r".*?"
        replacement = f"\n{new_stats_line}\n"
        
        updated_content = re.sub(pattern, replacement, content, flags=re.DOTALL)

        with open(README_PATH, "w", encoding="utf-8") as f:
            f.write(updated_content)
            
        print("✅ Stats metrics written successfully to README.")

    except Exception as e:
        print(f"❌ Execution failed: {e}")
        raise e

if __name__ == "__main__":
    main()
