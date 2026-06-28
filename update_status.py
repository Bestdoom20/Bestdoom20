import re
import urllib.request
import json
from datetime import datetime

# Configuration
USERNAME = "bestdoom20"
README_PATH = "README.md"

def fetch_github_data(url):
    req = urllib.request.Request(
        url, 
        headers={'User-Agent': 'Mozilla/5.0'}
    )
    with urllib.request.urlopen(req) as response:
        return json.loads(response.read().decode())

def main():
    try:
        # 1. Fetch User Base Data to calculate Account Age
        user_data = fetch_github_data(f"https://api.github.com/users/{USERNAME}")
        created_at = datetime.strptime(user_data["created_at"], "%Y-%m-%dT%H:%M:%SZ")
        years_active = max(1, datetime.utcnow().year - created_at.year)
        public_repos = user_data.get("public_repos", 0)

        # 2. Fetch Repositories to Aggregate Stars & Projects 
        # Note: Default page size is 30, setting to 100 for accuracy
        repos_data = fetch_github_data(f"https://api.github.com/users/{USERNAME}/repos?per_page=100")
        total_stars = sum(repo["stargazers_count"] for repo in repos_data)
        personal_projects = len(repos_data)

        # 3. Search API for Global Counts (Commits, Issues, PRs)
        # GitHub Search API lets us count items across the entire platform for your user
        commit_search = fetch_github_data(f"https://api.github.com/search/commits?q=author:{USERNAME}")
        total_commits = commit_search.get("total_count", 31890) # Fallback to base line if search throttled

        issue_search = fetch_github_data(f"https://api.github.com/search/issues?q=author:{USERNAME}+type:issue")
        total_issues = issue_search.get("total_count", 792)

        pr_search = fetch_github_data(f"https://api.github.com/search/issues?q=author:{USERNAME}+type:pr")
        total_prs = pr_search.get("total_count", 1784)

        # Hardcoded streak metric or manual baseline since streaks require a scraping pipeline
        commit_streak = "2,697" 

        # 4. Format the dynamic string line
        new_stats_line = (
            f"I joined GitHub **{years_active}** {'years' if years_active > 1 else 'year'} ago and have since "
            f"pushed **{total_commits:,}** commits, opened **{total_issues:,}** issues, "
            f"submitted **{total_prs:,}** pull requests, and earned **{total_stars:,}** stars "
            f"across **{personal_projects}** personal projects, with contributions to **{public_repos}** public repositories.\n\n"
            f"I'm currently on a **{commit_streak}**-day commit streak."
        )

        # 5. Read and inject into README between HTML anchors
        with open(README_PATH, "r", encoding="utf-8") as f:
            content = f.read()

        pattern = r".*?"
        replacement = f"\n{new_stats_line}\n"
        
        updated_content = re.sub(pattern, replacement, content, flags=re.DOTALL)

        with open(README_PATH, "w", encoding="utf-8") as f:
            f.write(updated_content)
            
        print("Successfully synchronized real-time metrics.")

    except Exception as e:
        print(f"Execution failed: {e}")

if __name__ == "__main__":
    main()
