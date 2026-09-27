"""Every word and number on the profile. Figures are checkable in the linked repositories."""

from dataclasses import dataclass

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


@dataclass(frozen=True)
class Project:
    slug: str
    name: str
    kind: str
    context: str
    lines: tuple[str, ...]  # tagline, pre-wrapped to fit the card
    metric: str
    metric_label: tuple[str, ...]
    stack: tuple[str, ...]
    repo: str


PROJECTS = (
    Project(
        slug="ghostops",
        name="GhostOps",
        kind="Autonomous incident response",
        context="AIOps · SRE · 2026",
        lines=(
            "Alertmanager fires; three CrewAI agents find the root",
            "cause, write a minimal patch and prove it in a Docker",
            "sandbox under OPA policy. Only then is a PR opened.",
        ),
        metric="2",
        metric_label=("real incidents fixed end to end,", "each shipped as a reviewed PR"),
        stack=("CrewAI", "Claude API", "FastAPI", "Kubernetes", "OPA"),
        repo=f"{GITHUB}/ghostops",
    ),
    Project(
        slug="aethermed",
        name="AetherMed",
        kind="Clinic booking, built to survive",
        context="ResilientCommerce · DevOps / SRE",
        lines=(
            "A Next.js booking app under production DevOps: HPA",
            "scales 2 to 8 pods under k6 load, ArgoCD self-heals",
            "from main, and Sentry, OTel and Jaeger trace it all.",
        ),
        metric="$0.03",
        metric_label=("for a real EKS, VPC and ALB stack,", "applied with Terraform, then destroyed"),
        stack=("Terraform", "AWS EKS", "ArgoCD", "k6", "Sentry"),
        repo=f"{GITHUB}/Aethermed",
    ),
    Project(
        slug="sahayak",
        name="Sahayak",
        kind="Farm to market, by conversation",
        context="Full-stack · applied AI",
        lines=(
            "Farmers list produce by chatting with a Gemini agent;",
            "live mandi prices come from Agmarknet, search runs on",
            "pgvector, and checkout goes through Razorpay.",
        ),
        metric="4",
        metric_label=("tools the agent calls: list, search,", "track an order, raise an emergency"),
        stack=("Next.js", "FastAPI", "Gemini", "pgvector", "Razorpay"),
        repo=f"{GITHUB}/sahayak",
    ),
    Project(
        slug="greencart",
        name="GreenCart",
        kind="Grocery commerce, MERN",
        context="Full-stack · Vercel",
        lines=(
            "A grocery store with a separate seller dashboard,",
            "Cloudinary product images, JWT cookie auth, and",
            "checkout by cash on delivery or Stripe.",
        ),
        metric="6",
        metric_label=("REST modules: users, sellers, products,", "cart, addresses and orders"),
        stack=("React", "Express", "MongoDB", "Stripe", "Tailwind"),
        repo=f"{GITHUB}/greencart",
    ),
)

# The notebook's rules, rewritten for how I build. (title, the rule, in its own words)
RULES = (
    ("Ship it, then armor it", "Deploy first; observability and", "guardrails follow within the hour."),
    ("Automate the boring", "CI/CD and agents own the routine.", "The judgment stays with me."),
    ("Verify before trusting", "A model may propose the fix; only a", "passing test or a human approves it."),
)
