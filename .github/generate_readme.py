#!/usr/bin/env python3
"""Regenerate the dynamic blocks in README.md from live GitHub data.

Fills <!-- START_STATS --> and <!-- START_PROJECTS --> sections.
Token: env GH_PAT (needs repo + read:user) or GITHUB_TOKEN fallback.
ponytail: single file, stdlib-only (urllib). No deps to install in CI.
"""
import json, os, sys, urllib.request, datetime as dt

USER = "Bestdoom20"
TOKEN = os.environ.get("GH_PAT") or os.environ.get("GITHUB_TOKEN")
if not TOKEN:
    sys.exit("no token in GH_PAT / GITHUB_TOKEN")
HDR = {"Authorization": f"bearer {TOKEN}", "User-Agent": USER}
TODAY = dt.date.fromisoformat(os.environ.get("TODAY") or dt.date.today().isoformat())


def gql(query, variables):
    body = json.dumps({"query": query, "variables": variables}).encode()
    req = urllib.request.Request("https://api.github.com/graphql", body, HDR)
    d = json.load(urllib.request.urlopen(req))
    if "errors" in d:
        sys.exit(json.dumps(d["errors"]))
    return d["data"]


def rest(path):
    req = urllib.request.Request(f"https://api.github.com{path}", headers=HDR)
    return json.load(urllib.request.urlopen(req))


def windows(created, today):
    """Yield <=1yr (from,to) ISO windows covering created..today (GraphQL caps at 1yr)."""
    cur = created
    while cur < today:
        nxt = min(dt.date(cur.year + 1, cur.month, cur.day) if (cur.month, cur.day) != (2, 29)
                  else dt.date(cur.year + 1, 3, 1), today)
        yield cur.isoformat() + "T00:00:00Z", nxt.isoformat() + "T23:59:59Z"
        cur = nxt + dt.timedelta(days=1)


CONTRIB_Q = """
query($login:String!,$from:DateTime!,$to:DateTime!){
  user(login:$login){
    contributionsCollection(from:$from,to:$to){
      totalCommitContributions
      totalIssueContributions
      totalPullRequestContributions
      restrictedContributionsCount
      contributionCalendar{ weeks{ contributionDays{ date contributionCount } } }
    }
  }
}"""


def main():
    user = rest(f"/users/{USER}")
    created = dt.datetime.fromisoformat(user["created_at"].replace("Z", "+00:00")).date()
    years = max(1, (TODAY - created).days // 365)

    commits = issues = prs = 0
    daymap = {}
    for fr, to in windows(created, TODAY):
        c = gql(CONTRIB_Q, {"login": USER, "from": fr, "to": to})["user"]["contributionsCollection"]
        commits += c["totalCommitContributions"] + c["restrictedContributionsCount"]
        issues += c["totalIssueContributions"]
        prs += c["totalPullRequestContributions"]
        for w in c["contributionCalendar"]["weeks"]:
            for day in w["contributionDays"]:
                daymap[day["date"]] = daymap.get(day["date"], 0) + day["contributionCount"]

    # current streak: consecutive days with >0 ending today (or yesterday if today still 0)
    streak, d = 0, TODAY
    if daymap.get(d.isoformat(), 0) == 0:
        d -= dt.timedelta(days=1)
    while daymap.get(d.isoformat(), 0) > 0:
        streak += 1
        d -= dt.timedelta(days=1)

    repos = rest(f"/user/repos?affiliation=owner&per_page=100&sort=pushed")
    stars = sum(r["stargazers_count"] for r in repos)
    projects = len(repos)

    yr = "year" if years == 1 else "years"
    stats = (
        f"I joined GitHub **{years}** {yr} ago and have since pushed **{commits:,}** commits, "
        f"opened **{issues:,}** issues, submitted **{prs:,}** pull requests, and earned "
        f"**{stars:,}** stars across **{projects}** personal projects.\n\n"
        f"I'm currently on a **{streak}**-day commit streak."
    )

    # projects table: most-recently-pushed repos, all languages each
    rows = []
    feature = [r for r in repos if r["name"].lower() != USER.lower()]
    for r in feature[:6]:
        langs = rest(f"/repos/{r['full_name']}/languages")
        lang = ", ".join(langs.keys()) or (r["language"] or "—")
        rows.append(
            f"| [{r['name']}]({r['html_url']}) | {ago(r['pushed_at'])} | {lang} | "
            f"{(r['description'] or '—').strip()} |"
        )
    table = ("| Repository | Last Commit | Languages | Description |\n"
             "|------------|------------|-----------|-------------|\n" + "\n".join(rows))

    patch("README.md", "STATS", stats)
    patch("README.md", "PROJECTS", table)
    print(f"commits={commits} stars={stars} projects={projects} streak={streak}")


def ago(iso):
    when = dt.datetime.fromisoformat(iso.replace("Z", "+00:00")).date()
    n = (TODAY - when).days
    if n <= 0: return "today"
    if n == 1: return "yesterday"
    if n < 30: return f"{n} days ago"
    if n < 365: return f"{n // 30} month{'s' if n // 30 > 1 else ''} ago"
    return f"{n // 365} year{'s' if n // 365 > 1 else ''} ago"


def patch(path, name, content):
    s, e = f"<!-- START_{name} -->", f"<!-- END_{name} -->"
    txt = open(path, encoding="utf-8").read()
    i, j = txt.index(s) + len(s), txt.index(e)
    open(path, "w", encoding="utf-8").write(txt[:i] + "\n" + content + "\n" + txt[j:])


if __name__ == "__main__":
    main()
