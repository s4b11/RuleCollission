import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def env(name: str, default: str = "") -> str:
    return os.environ.get(name, default)


DATABASE_URL = env("DATABASE_URL", f"sqlite:///{ROOT / 'data' / 'rulecollision.db'}")
JWT_SECRET = env("JWT_SECRET", "dev-only-secret-change-me-before-deploying")
AGENT_API_KEY = env("AGENT_API_KEY", "dev-agent-key")
WEB_APP_URL = env("WEB_APP_URL", "http://localhost:5173")
CORS_ORIGINS = [o for o in env("CORS_ORIGINS", "http://localhost:5173").split(",") if o]
SEED_DEMO = env("SEED_DEMO", "1") == "1"
DEMO_PASSWORD = env("DEMO_PASSWORD", "demo1234")
RULEPACK_DIR = Path(env("RULEPACK_DIR", str(ROOT / "rulepacks")))
FILES_DIR = Path(env("FILES_DIR", str(ROOT / "data" / "files")))

LIVEKIT_URL = env("LIVEKIT_URL")
LIVEKIT_API_KEY = env("LIVEKIT_API_KEY")
LIVEKIT_API_SECRET = env("LIVEKIT_API_SECRET")
LIVEKIT_AGENT_NAME = env("LIVEKIT_AGENT_NAME", "rulecollision")

GROQ_API_KEY = env("GROQ_API_KEY")
GROQ_MODEL = env("GROQ_MODEL", "openai/gpt-oss-120b")
OPENAI_API_KEY = env("OPENAI_API_KEY")
OPENAI_MODEL = env("OPENAI_MODEL", "gpt-5.4-mini")

R2_ENDPOINT = env("R2_ENDPOINT")
R2_ACCESS_KEY_ID = env("R2_ACCESS_KEY_ID")
R2_SECRET_ACCESS_KEY = env("R2_SECRET_ACCESS_KEY")
R2_BUCKET = env("R2_BUCKET", "rulecollision")

EMBEDDER = env("EMBEDDER", "auto")
PHONE_SESSION_SECONDS = int(env("PHONE_SESSION_SECONDS", "180"))
