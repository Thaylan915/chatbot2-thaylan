import os
from pathlib import Path

try:
    from dotenv import load_dotenv
    # Force values from .env to avoid stale OS/session env vars overriding DB config.
    load_dotenv(encoding="utf-8", override=True)
except ImportError:
    pass


def _normalize_gemini_model(value: str, default: str) -> str:
    model = os.getenv(value, default)
    return model if model.startswith("models/") else f"models/{model}"

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = os.getenv("SECRET_KEY", "django-insecure-substitua-em-producao")
DEBUG = os.getenv("DEBUG", "True") == "True"
ALLOWED_HOSTS = os.getenv("ALLOWED_HOSTS", "localhost,127.0.0.1").split(",")

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "corsheaders",
    "rest_framework",
    "rest_framework_simplejwt",
    "Backend.app",
    "Backend.app.documents",
]

MIDDLEWARE = [
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": os.getenv("POSTGRES_DB", "chatbot"),
        "USER": os.getenv("POSTGRES_USER", "chatbot_user"),
        "PASSWORD": os.getenv("POSTGRES_PASSWORD", "chatbot_pass"),
        "HOST": os.getenv("DB_HOST", "localhost"),
        "PORT": os.getenv("DB_PORT", "5433"),
    }
}

REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": (
        "rest_framework_simplejwt.authentication.JWTAuthentication",
    ),
}

from datetime import timedelta
SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME":  timedelta(hours=12),  # antes era 5 min (default)
    "REFRESH_TOKEN_LIFETIME": timedelta(days=7),
}

CORS_ALLOWED_ORIGINS = [
    "http://localhost:5173",
    "http://localhost:3000",
]

LANGUAGE_CODE = "pt-br"
TIME_ZONE = "America/Sao_Paulo"
USE_I18N = True
USE_TZ = True

STATIC_URL = "/static/"
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
CHAT_MODEL = _normalize_gemini_model("CHAT_MODEL", "gemini-flash-latest")
EMBEDDING_MODEL = _normalize_gemini_model("EMBEDDING_MODEL", "text-embedding-004")

# Número de chunks finais enviados ao LLM como contexto
TOP_K = int(os.getenv("TOP_K", 5))

# Candidatos buscados no pgvector antes do re-ranking MMR (deve ser > TOP_K)
# Valores maiores melhoram a diversidade do contexto ao custo de mais memória
RERANK_FETCH_K = int(os.getenv("RERANK_FETCH_K", TOP_K * 4))
