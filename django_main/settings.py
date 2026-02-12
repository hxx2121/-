import os
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent.parent

try:
    from dotenv import load_dotenv

    load_dotenv(BASE_DIR / ".env")
except Exception:
    pass


SECRET_KEY = os.environ.get("DJANGO_SECRET_KEY", "unsafe-secret-key")
DEBUG = os.environ.get("DJANGO_DEBUG", "1") == "1"
ALLOWED_HOSTS = [
    host.strip()
    for host in os.environ.get("DJANGO_ALLOWED_HOSTS", "localhost,127.0.0.1").split(",")
    if host.strip()
]


INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    # 新增的app
    "rest_framework",
    "rest_framework.authtoken",
    "django_auth",
    "django_utils",
    "django_qa",
]


MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]


ROOT_URLCONF = "django_main.urls"


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
    }
]


WSGI_APPLICATION = "django_main.wsgi.application"
ASGI_APPLICATION = "django_main.asgi.application"


# DATABASES = {
#     "default": {
#         "ENGINE": "django.db.backends.sqlite3",
#         "NAME": BASE_DIR / "database/db.sqlite3",
#     }
# }

# MySQL Configuration (Uncomment to use MySQL)
# DATABASES = {
#     'default': {
#         'ENGINE': 'django.db.backends.mysql',
#         'NAME': 'programming_qa_system',
#         'USER': 'root',
#         'PASSWORD': '123456',
#         'HOST': 'localhost',
#         'PORT': '3306',
#     }
# }

# SQLite Configuration
DJANGO_DB_ENGINE = (os.environ.get("DJANGO_DB_ENGINE", "sqlite3") or "sqlite3").strip().lower()
if DJANGO_DB_ENGINE in {"mysql", "django.db.backends.mysql"}:
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.mysql",
            "NAME": os.environ.get("MYSQL_DATABASE", "root"),
            "USER": os.environ.get("MYSQL_USER", "root"),
            "PASSWORD": os.environ.get("MYSQL_PASSWORD", "123456"),
            "HOST": os.environ.get("MYSQL_HOST", "localhost"),
            "PORT": os.environ.get("MYSQL_PORT", "3306"),
            "OPTIONS": {"charset": "utf8mb4"},
        }
    }
else:
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": BASE_DIR / "database/db.sqlite3",
        }
    }

# Model Selection Configuration
# Options: 'qwen', 'doubao-pro', 'gpt-4-code', 'codellama', 'starcoder', 'ollama:llama3', etc.
CURRENT_LLM_MODEL = os.environ.get("CURRENT_LLM_MODEL", "qwen")

# Ollama Configuration
OLLAMA_API_BASE = os.environ.get("OLLAMA_API_BASE", "http://localhost:11434")
OLLAMA_MODEL_CODELLAMA = os.environ.get("OLLAMA_MODEL_CODELLAMA", "codellama:7b-instruct")
OLLAMA_MODEL_STARCODER = os.environ.get("OLLAMA_MODEL_STARCODER", "starcoder2")

# Qwen (Tongyi Qianwen) Configuration
# 兼容 OpenAI 格式
QWEN_API_KEY = os.environ.get("QWEN_API_KEY", "")
QWEN_API_BASE = os.environ.get("QWEN_API_BASE", "https://dashscope.aliyuncs.com/compatible-mode/v1")
# Qwen Coder Turbo 是阿里云针对编程优化的模型
QWEN_MODEL_NAME = os.environ.get("QWEN_MODEL_NAME", "qwen-coder-turbo")
OLLAMA_MODEL_STARCODER = os.environ.get("OLLAMA_MODEL_STARCODER", "starcoder2")

# Selected optimal model after comparison: CodeLlama-34b / GPT-4 Code equivalent
ARK_LLM_TEXT_MODEL_ID = os.environ.get("ARK_LLM_TEXT_MODEL_ID", "doubao-1-5-pro-32k-250115")
ARK_LLM_EMBEDDING_MODEL_ID = os.environ.get("ARK_LLM_EMBEDDING_MODEL_ID", "doubao-embedding-text-240715")


AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]


LANGUAGE_CODE = "zh-hans"
TIME_ZONE = "Asia/Shanghai"
USE_I18N = True
USE_TZ = True


STATIC_URL = "static/"
MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"


DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"


REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": (
        "rest_framework.authentication.TokenAuthentication",
    ),
    "EXCEPTION_HANDLER": "django_auth.utils.exception_handler.custom_exception_handler",
}
