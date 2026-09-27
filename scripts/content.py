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

# Scenes from the Death Note anime, embedded straight from Tenor: GitHub loads them for
# the viewer. (name: (url, alt text)). scripts/cinema.py can cut graded versions of these.
CLIPS = {
    "ryuk-moon": ("https://media.tenor.com/tKMTWPmmGaUAAAAC/ryuk-death-note.gif", "Ryuk flying past the moon"),
    "light-smile": ("https://media.tenor.com/F9Yh5L2g3AYAAAAC/light-yagami.gif", "Light Yagami's smile, a red glint in his eye"),
    "ryuk-eyes": ("https://media.tenor.com/rW61ogX4gj8AAAAC/ryuk-death-note.gif", "Ryuk's glowing red eyes"),
    "l-stare": ("https://media.tenor.com/DiQoAtvjMzoAAAAC/death-note-l-death-note.gif", "L staring out of the dark"),
    "ryuk-school": ("https://media.tenor.com/fcUrOX_xwEgAAAAC/death-note-anime.gif", "Ryuk looming behind Light at school"),
    "light-writing": ("https://media.tenor.com/32H8OJbPIlAAAAAC/death-note-light.gif", "Light writing in the Death Note"),
    "pen": ("https://media.tenor.com/1ybUFYQpNDgAAAAC/death-note-light-yagami.gif", "The pen moving across the note"),
    "light-laugh": ("https://media.tenor.com/llfBQe-pZjIAAAAC/joblife-jl.gif", "Light's shadowed, red-eyed laugh"),
    "ryuk-red": ("https://media.tenor.com/SEy40M8j7k8AAAAC/ryuk-death-note.gif", "Ryuk lit red"),
    "ryuk-tower": ("https://media.tenor.com/0S-qY1MlqDAAAAAC/death-note-anime.gif", "Ryuk perched on a tower at sunset"),
}
