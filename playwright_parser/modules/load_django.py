import os
import sys
import django

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..','braincom_playwright')))
os.environ['DJANGO_SETTINGS_MODULE'] = 'braincom_playwright.settings'
django.setup()


if __name__ == "__main__":
    from django.conf import settings
    print(settings.DATABASES['default']['NAME'])