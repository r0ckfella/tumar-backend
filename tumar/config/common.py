import os

from decouple import config
from configurations import Configuration
from dj_database_url import parse as db_url

from django.utils.translation import gettext_lazy as _

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


class Common(Configuration):
    INSTALLED_APPS = (
        "django.contrib.admin",
        "django.contrib.auth",
        "django.contrib.contenttypes",
        "django.contrib.sessions",
        "django.contrib.messages",
        "django.contrib.staticfiles",
        "django.contrib.gis",  # geodjango support
        # Third party apps
        "rest_framework",  # utilities for rest apis
        "rest_framework_gis",
        "rest_framework.authtoken",  # token authentication
        "django_filters",  # for filtering rest endpoints
        "admin_reorder",
        "memcache_status",
        "drf_yasg",
        "push_notifications",
        # Registration related
        # "django.contrib.sites",
        # Your apps
        "tumar.users.apps.UsersConfig",
        "tumar.animals.apps.AnimalsConfig",
        "tumar.indicators.apps.IndicatorsConfig",
        "tumar.ecalendar.apps.EcalendarConfig",
        "tumar.catalog.apps.CatalogConfig",
        "tumar.community.apps.CommunityConfig",
        "tumar.dashboard.apps.DashboardConfig",
        "tumar.notify.apps.NotifyConfig",
        "tumar.usersupport.apps.UsersupportConfig",
    )

    # https://docs.djangoproject.com/en/2.0/topics/http/middleware/
    MIDDLEWARE = (
        "django.middleware.security.SecurityMiddleware",
        "django.contrib.sessions.middleware.SessionMiddleware",
        "django.middleware.locale.LocaleMiddleware",
        "django.middleware.common.CommonMiddleware",
        "django.middleware.csrf.CsrfViewMiddleware",
        "django.contrib.auth.middleware.AuthenticationMiddleware",
        "django.contrib.messages.middleware.MessageMiddleware",
        "django.middleware.clickjacking.XFrameOptionsMiddleware",
        "admin_reorder.middleware.ModelAdminReorder",
    )

    ALLOWED_HOSTS = ["*"]
    ROOT_URLCONF = "tumar.urls"
    SECRET_KEY = config("DJANGO_SECRET_KEY")
    WSGI_APPLICATION = "tumar.wsgi.application"

    FILE_UPLOAD_PERMISSIONS = 0o644

    # Email
    EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"

    ADMINS = (("Author", "epmek96@gmail.com"),)

    # Postgres
    DATABASES = {
        "default": config("TUMAR_DB", cast=db_url),
    }
    # DATABASES['default']['ENGINE'] = 'django.contrib.gis.db.backends.postgis'

    # General
    APPEND_SLASH = False
    TIME_ZONE = "Asia/Almaty"
    LANGUAGE_CODE = "ru"
    LANGUAGES = [
        ("en", _("English")),
        ("ru", _("Russian")),
    ]
    SITE_ROOT = os.path.dirname(os.path.realpath(__name__))
    LOCALE_PATHS = [os.path.join(SITE_ROOT, "locale")]

    # If you set this to False, Django will make some optimizations so as not
    # to load the internationalization machinery.
    USE_I18N = True
    USE_L10N = True
    USE_TZ = True
    LOGIN_REDIRECT_URL = "/"

    # Static files (CSS, JavaScript, Images)
    # https://docs.djangoproject.com/en/2.0/howto/static-files/
    STATIC_ROOT = os.path.normpath(os.path.join(os.path.dirname(BASE_DIR), "static"))
    STATICFILES_DIRS = []
    STATIC_URL = "/static/"
    STATICFILES_FINDERS = (
        "django.contrib.staticfiles.finders.FileSystemFinder",
        "django.contrib.staticfiles.finders.AppDirectoriesFinder",
    )

    # Media files
    MEDIA_ROOT = os.path.join(os.path.dirname(BASE_DIR), "media")
    MEDIA_URL = "/media/"

    TEMPLATES = [
        {
            "BACKEND": "django.template.backends.django.DjangoTemplates",
            "DIRS": STATICFILES_DIRS,
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

    # Set DEBUG to False as a default for safety
    # https://docs.djangoproject.com/en/dev/ref/settings/#debug
    DEBUG = config("DJANGO_DEBUG", default=False, cast=bool)

    # Password Validation
    # https://docs.djangoproject.com/en/2.0/topics/auth/passwords/#module-django.contrib.auth.password_validation
    AUTH_PASSWORD_VALIDATORS = [
        {
            "NAME": "django.contrib.auth.password_validation"
            + ".UserAttributeSimilarityValidator",
        },
        {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
        {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
        {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
    ]

    # Logging
    LOGGING = {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "verbose": {
                "format": "%(levelname)s %(asctime)s %(module)s %(process)d %(thread)d"
                + " %(message)s"
            },
            "simple": {"format": "[%(levelname)s] %(message)s"},
        },
        "filters": {"require_debug_true": {"()": "django.utils.log.RequireDebugTrue"}},
        "handlers": {
            "console": {
                "level": "DEBUG",
                "class": "logging.StreamHandler",
                "formatter": "simple",
            },
        },
        "loggers": {
            "": {"handlers": ["console"], "level": "INFO"},
            "django": {"handlers": ["console"], "level": "INFO", "propagate": False},
        },
    }

    # Custom user app
    AUTH_USER_MODEL = "users.User"

    # Django Rest Framework
    REST_FRAMEWORK = {
        "DEFAULT_PAGINATION_CLASS": "rest_framework.pagination.PageNumberPagination",
        "PAGE_SIZE": config("DJANGO_PAGINATION_LIMIT", default=30, cast=int),
        "DATETIME_FORMAT": "%Y-%m-%dT%H:%M:%S%z",
        "DEFAULT_RENDERER_CLASSES": ("rest_framework.renderers.JSONRenderer",),
        "DEFAULT_PERMISSION_CLASSES": ["rest_framework.permissions.IsAuthenticated"],
        "DEFAULT_AUTHENTICATION_CLASSES": (
            "rest_framework.authentication.TokenAuthentication",
            "rest_framework.authentication.SessionAuthentication",
        ),
    }

    USERNAME_VALIDATORS = [
        "tumar.users.models.main_validator",
    ]

    ADMIN_REORDER = (
        "animals",
        "catalog",
        "community",
        "ecalendar",
        "indicators",
        {"app": "push_notifications", "models": ("push_notifications.GCMDevice", "push_notifications.APNSDevice")},
        {"app": "users", "models": ("users.User", "auth.Group", "authtoken.Token")},
    )

    DOWNLOAD_GEOLOCATIONS_URL = config("DOWNLOAD_GEOLOCATIONS_URL")
    DOWNLOAD_GEOLOCATIONS_URL_2 = config("DOWNLOAD_GEOLOCATIONS_URL_2")
    GET_BATTERY_CHARGE_URL = config("GET_BATTERY_CHARGE_URL")
    CHINESE_API_KEY = config("CHINESE_API_KEY")
    CHINESE_LOGIN_URL = config("CHINESE_LOGIN_URL")
    EGISTIC_CADASTRE_QUERY_URL = config("EGISTIC_CADASTRE_QUERY_URL")
    EGISTIC_LOGIN_URL = config("EGISTIC_LOGIN_URL")
    EGISTIC_USERNAME = config("EGISTIC_USERNAME")
    EGISTIC_PASSWORD = config("EGISTIC_PASSWORD")
    STANDARD_LOGIN_PASSWORD = config("STANDARD_LOGIN_PASSWORD")

    DAYS_BETWEEN_IMAGERY_REQUESTS = 5

    CACHES = {
        "default": {
            "BACKEND": "django.core.cache.backends.memcached.MemcachedCache",
            "LOCATION": config("MEMCACHED_ADDRESS"),
        }
    }

    SWAGGER_SETTINGS = {
        "SECURITY_DEFINITIONS": {
            "DRF Token": {"type": "apiKey", "name": "Authorization", "in": "header"}
        }
    }
