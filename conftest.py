"""
Configuração mínima do Django para os testes unitários.
Evita a necessidade de um banco de dados real ou variáveis de ambiente.
"""
import django
from django.conf import settings


def pytest_configure():
    if not settings.configured:
        settings.configure(
            DATABASES={
                "default": {
                    "ENGINE": "django.db.backends.sqlite3",
                    "NAME":   ":memory:",
                }
            },
            INSTALLED_APPS=[
                "django.contrib.contenttypes",
                "django.contrib.auth",
                "Backend.app",
                "Backend.app.documents",
            ],
            GEMINI_API_KEY="fake-key-for-tests",
            CHAT_MODEL="gemini-1.5-flash",
            EMBEDDING_MODEL="models/text-embedding-004",
            TOP_K=3,
            RERANK_FETCH_K=12,
            DEFAULT_AUTO_FIELD="django.db.models.BigAutoField",
            USE_TZ=True,
        )
        django.setup()
