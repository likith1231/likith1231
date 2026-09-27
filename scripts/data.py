"""Everything live on the profile, read from GitHub's GraphQL API.

With GITHUB_TOKEN set (the refresh workflow sets it), every number is real. Without one,
the build still runs on SAMPLE data so the design can be previewed; the cards then say
"preview data" in their footers.
"""

import json
import os
import sys
import urllib.request
from dataclasses import dataclass, field
from datetime import date, datetime, timedelta, timezone

USER = "likith1231"
SKIP_REPOS = {USER}  # the profile repo itself isn't a project

QUERY = """
query($login: String!) {
  user(login: $login) {
    createdAt
    contributionsCollection {
      contributionCalendar {
        totalContributions
        weeks { contributionDays { date contributionCount } }
      }
    }
    repositories(ownerAffiliations: OWNER, isFork: false, privacy: PUBLIC, first: 100,
                 orderBy: {field: PUSHED_AT, direction: DESC}) {
      totalCount
      nodes {
        name description url stargazerCount pushedAt
        primaryLanguage { name color }
        languages(first: 10, orderBy: {field: SIZE, direction: DESC}) { edges { size node { name color } } }
      }
    }
  }
}
"""


@dataclass
class Repo:
    name: str
    description: str
    url: str
    stars: int
    pushed: date
    language: str
    color: str


@dataclass
class Profile:
    live: bool
    today: date
    since: int                      # year the account was created
    contributions: int              # last year
    days: list[tuple[date, int]]    # the contribution calendar, oldest first
    repos: list[Repo]
    repo_count: int
    stars: int
    languages: list[tuple[str, str, float]] = field(default_factory=list)  # (name, colour, share)

    @property
    def last30(self) -> list[int]:
        return [n for _, n in self.days[-30:]]

    @property
    def active30(self) -> int:
        return sum(1 for n in self.last30 if n)

    @property
    def current_streak(self) -> int:
        """Consecutive active days up to today; a quiet today doesn't break it yet."""
        counts = [n for _, n in self.days]
        if counts and counts[-1] == 0:
            counts = counts[:-1]
        streak = 0
        for n in reversed(counts):
            if not n:
                break
            streak += 1
        return streak

    @property
    def longest_streak(self) -> int:
        best = run = 0
        for _, n in self.days:
            run = run + 1 if n else 0
            best = max(best, run)
        return best


def _query(token: str) -> dict:
    request = urllib.request.Request(
        "https://api.github.com/graphql",
        data=json.dumps({"query": QUERY, "variables": {"login": USER}}).encode(),
        headers={"Authorization": f"bearer {token}", "Content-Type": "application/json"},
    )
    with urllib.request.urlopen(request, timeout=30) as response:
        payload = json.load(response)
    if "errors" in payload:
        raise ValueError(payload["errors"])
    return payload["data"]["user"]


def _from_api(user: dict) -> Profile:
    calendar = user["contributionsCollection"]["contributionCalendar"]
    days = [
        (date.fromisoformat(d["date"]), d["contributionCount"])
        for week in calendar["weeks"] for d in week["contributionDays"]
    ]
    nodes = [n for n in user["repositories"]["nodes"] if n["name"] not in SKIP_REPOS]
    repos = [
        Repo(
            name=n["name"], description=(n["description"] or "").strip(), url=n["url"],
            stars=n["stargazerCount"], pushed=datetime.fromisoformat(n["pushedAt"].replace("Z", "+00:00")).date(),
            language=(n["primaryLanguage"] or {}).get("name", ""), color=(n["primaryLanguage"] or {}).get("color") or "#888888",
        )
        for n in nodes
    ]
    sizes: dict[str, list] = {}
    for n in nodes:
        for edge in n["languages"]["edges"]:
            entry = sizes.setdefault(edge["node"]["name"], [edge["node"]["color"] or "#888888", 0])
            entry[1] += edge["size"]
    total = sum(v[1] for v in sizes.values()) or 1
    languages = sorted(((k, v[0], v[1] / total) for k, v in sizes.items()), key=lambda x: -x[2])
    return Profile(
        live=True, today=days[-1][0], since=int(user["createdAt"][:4]),
        contributions=calendar["totalContributions"], days=days, repos=repos,
        repo_count=len(nodes), stars=sum(r.stars for r in repos), languages=languages,
    )


def _sample() -> Profile:
    """Plausible stand-in numbers, used only when there is no token to read the real ones."""
    today = datetime.now(timezone.utc).date()
    pattern = [0, 2, 5, 0, 1, 7, 3, 0, 0, 4, 9, 2, 0, 1, 6, 0, 3, 8, 12, 4, 0, 0, 2, 5, 7, 3, 1, 6, 11, 4]
    days = [(today - timedelta(days=364 - i), pattern[i % len(pattern)] if i % 7 else 0) for i in range(365)]
    days[-30:] = [(d, pattern[i]) for i, (d, _) in enumerate(days[-30:])]
    repos = [
        Repo("tuf-solutions", "Java solutions to the TUF A2Z sheet, one problem a day, automated.",
             f"https://github.com/{USER}/tuf-solutions", 0, today, "Java", "#b07219"),
        Repo("greencart", "Grocery store with a seller dashboard, Stripe checkout and Cloudinary images.",
             f"https://github.com/{USER}/greencart", 0, today - timedelta(days=3), "JavaScript", "#f1e05a"),
        Repo("Aethermed", "Clinic booking on Next.js, wrapped in EKS, ArgoCD, HPA and OpenTelemetry.",
             f"https://github.com/{USER}/Aethermed", 0, today - timedelta(days=3), "TypeScript", "#3178c6"),
        Repo("ghostops", "Autonomous AIOps: detects an incident, patches it, proves it, opens the PR.",
             f"https://github.com/{USER}/ghostops", 0, today - timedelta(days=41), "Python", "#3572A5"),
    ]
    languages = [("TypeScript", "#3178c6", 0.34), ("Python", "#3572A5", 0.22), ("JavaScript", "#f1e05a", 0.18),
                 ("Java", "#b07219", 0.12), ("HCL", "#844FBA", 0.08), ("CSS", "#563d7c", 0.06)]
    return Profile(
        live=False, today=today, since=2024, contributions=sum(n for _, n in days), days=days,
        repos=repos, repo_count=9, stars=0, languages=languages,
    )


def load() -> Profile:
    token = os.environ.get("GITHUB_TOKEN")
    if token:
        try:
            return _from_api(_query(token))
        except (OSError, KeyError, TypeError, ValueError) as error:
            print(f"GitHub data unavailable, using preview data: {error}", file=sys.stderr)
    return _sample()
