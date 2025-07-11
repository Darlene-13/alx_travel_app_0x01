"""
Django settings for alx_travel_app project.

Generated by 'django-admin startproject' using Django 5.2.2.

For more information on this file, see
https://docs.djangoproject.com/en/5.2/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/5.2/ref/settings/
"""

from pathlib import Path # Modern OS safe way to handle filesystem paths
import os
import environ
from decouple import config


# Initializing django environment
env = environ.Env(
    # set casting and default values
    DEBUG=(bool, False) # Notes that Debug is expected to be returned as a boolean env variables but take note, that debug takes the default False esp for production cases.
)
# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent


# Read environmental variables from the .env files, this one loads the .env file where we store secret variables
environ.Env.read_env(os.path.join(BASE_DIR,'.env'))
# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/5.2/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = env('SECRET_KEY')

# Chapa API configuration
CHAPA_SECRET_KEY = config('CHAPA_SECRET_KEY')
CHAPA_PUBLIC_KEY = config('CHAPA_PUBLIC_KEY')
CHAPA_BASE_URL = config('CHAPA_BASE_URL')

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = env('DEBUG')  # To enble debug mode. SInce we do not debug in production, debug mode is always False

ALLOWED_HOSTS = []  # List of hostnames that djangowill serve it could be something like "yourdoman.com"


# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'listings', # Local apps

    # Thirs party apps
    'rest_framework',
    'corsheaders',
    'drf_yasg',
]

# Middlwares are a chain of components in between the request and response, upon a request, thye can modify, check, block or let it through.

MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',   # To allow cross-origin requests
    'django.middleware.security.SecurityMiddleware', # Add security headers
    'django.contrib.sessions.middleware.SessionMiddleware', # enables django sessions (cookies)
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware', # Protection against cross site request forgery attacks
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'alx_travel_app.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR/ 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]


#This is like a translator between the web server and django app...
WSGI_APPLICATION = 'alx_travel_app.wsgi.application' # WEb server gateway interface, this is standard way for python apps to talk to the webserver


# Database
# https://docs.djangoproject.com/en/5.2/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': env('DB_NAME'), # Place holder name
        'USER': env('DB_USER'),
        'PASSWORD' : env('DB_PASSWORD'),
        'HOST': env('DB_HOST'),
        'PORT': env('DB_PORT'),
        'OPTIONS' : {
            'init_command':"SET sql_mode = 'STRICT_TRANS_TABLES'"
        },


    }
}


# Password validation
# https://docs.djangoproject.com/en/5.2/ref/settings/#auth-password-validators


#Password validators
AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]


# Internationalization
# https://docs.djangoproject.com/en/5.2/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/5.2/howto/static-files/

STATIC_URL = 'static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_DIRS = [
    BASE_DIR / 'static', # For development purposes
]
# Default primary key field type
# https://docs.djangoproject.com/en/5.2/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'


# Django rest framework configuration
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework.authentication.SessionAuthentication',
        'rest_framework.authentication.TokenAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticatedOrReadOnly',
    ],
   'DEFAULT_PAGINATION_CLASSES':
       'rest_framework.pagination.PageNumberPagination',
       'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
       'PAGE_SIZE': 20, # Number of items per page
       'DEFAULT_RENDERER_CLASSES':[
           'rest_framework.renderers.JSONRenderer',
           'rest_framework.renderers.BrowsableAPIRenderer'
       ],
}

# Cors configuration
#Settings that allow frontend applicatoons to make requests to our API
CORS_ALLOWED_ORIGINS = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "http://localhost:8080",
]

# Allow credentials to be included in the CORS request
CORS_ALLOW_CREDENTIALS = True

# Allow all headers in CORS requests
CORS_ALLOW_ALL_HEADERS = True

# Swagger settings
#They define how authentication will be handled in swagger UI
#Swagger is meant to automatically document API, validating it, the requests and everything.
# Swagger also tests our API endpoints
SWAGGER_SETTINGS = {
    'SECURITY_DEFINITIONS': {
        # Token = label that will appear in Swagger UI
        'Token' :{ 
            'type': 'apiKey', # says that auth is done via the api key and not JWT built-in,in django, the API KEY is usually token-based-auth where the HTTP request is sent
            'name': 'Authorization', # name of the HTTP header, swagger will prompt the user to enter the token and then it will send this header
            'in': 'header' # specifies that the token will go the header
        }

        # It's like telling swagger My API expects token authentication via HTTP authorization Header
    },
    'USE_SESSION_AUTH': False, # Tells swagger that it should not allow the option to login via Django Session Auth
    'JSON_EDITOR': True,  #Allows the editting of the request header as JSON raw file this is useful when testing the POST and PUT requests
    'SUP[PORTED_SUBMIT_METHODS': [
        'get',
        'post',
        'put',
        'delete',
        'patch'
    ],
}

#Celery configuration (for background tasks)
CELERY_BROKER_URL = 'amqp://localhost' # RabbitMQ broker....Tells celery which broker to use, the broker is like a task queue
# The broker stores task that are waiting to be run AMPQ = Advaned Message Queueing Protocal that runs locally
CELERY_RESULT_BACKEND = 'django-db' # Tells celery where to store the task results
CELERY_ACCEPT_CONTENT = ['json'] # Upon sending a task it is converted to JSON
CELERY_TASK_SERIALIZER = 'json', # Upon storing the task, it is stored as a JSON
CELERY_RESULT_SERIALIZER = 'json',
CELERY_TIMEZONE = TIME_ZONE  #Tells celery which timezone to use when handling tasks that are time dependent


#Logging configuration
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,  # Allow exisiting loggers to continue working
    'handlers': { #Defines where the log messages go to....
        'file':{
            'level': 'INFO',
            'class' : 'logging.FileHandler',
            'filename': BASE_DIR / 'logs'/ 'django.log',
        },
        'console': { # Prints the lohgs to the console
            'level': 'DEBUG', 
            'class': 'logging.StreamHandler',
        },
    },
    'loggers': {
        'django': {
            'handlers': ['file', 'console'],
            'level': 'INFO',
            'propagate': True,
        },
    },
}