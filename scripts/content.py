"""Every word and number on the profile. Figures are checkable in the linked repositories."""

USER = "likith1231"
GITHUB = f"https://github.com/{USER}"
HOST = "likith@deathnote"

LINKS = {
    "linkedin": "https://www.linkedin.com/in/likith-lochan-2ab93b290",
    "email": "mailto:likithlu3@gmail.com",
    "github": f"{GITHUB}?tab=repositories",
}

# (key, value) rows of the whoami card, in groups separated by a rule.
WHOAMI: tuple[tuple[tuple[str, str], ...], ...] = (
    (
        ("role", "CS undergrad · B.E."),
        ("college", "APS College of Engineering"),
        ("focus", "DevOps · Backend/Full-Stack · Applied AI"),
    ),
    (
        ("langs", "Python · TypeScript · JavaScript · Java"),
        ("frontend", "React · Next.js · Tailwind · Three.js"),
        ("backend", "FastAPI · Node/Express · Socket.IO"),
        ("ai", "Claude · Gemini · CrewAI · pgvector RAG"),
        ("infra", "K8s · Terraform · EKS · ArgoCD · Vault"),
        ("observe", "Prometheus · Grafana · OTel · Sentry"),
        ("data", "PostgreSQL · Neon · Prisma · SQLAlchemy"),
    ),
    (
        ("crew", "Claude + Gemini + Antigravity, in parallel"),
        ("proof", "2 incidents fixed end-to-end by GhostOps"),
    ),
)
STATUS = "open to DevOps/Cloud · Backend · SDE · AI/ML"


# Rule I of the Death Note, quoted as it is written inside the cover.
EPIGRAPH = "\u201cThe human whose name is written in this note shall die.\u201d"

# The notebook's rules, rewritten for how I build. (title, the rule, in its own words)
RULES = (
    ("Ship it, then armor it", "Deploy first; observability and", "guardrails follow within the hour."),
    ("Automate the boring", "CI/CD and agents own the routine.", "The judgment stays with me."),
    ("Verify before trusting", "A model may propose the fix; only a", "passing test or a human approves it."),
)
