from django.conf import settings
from django.middleware.locale import LocaleMiddleware
from django.utils import translation


class EnglishDefaultLocaleMiddleware(LocaleMiddleware):
    def process_request(self, request):
        language_cookie = request.COOKIES.get(settings.LANGUAGE_COOKIE_NAME)
        if language_cookie:
            return super().process_request(request)

        language = translation.get_supported_language_variant(settings.LANGUAGE_CODE)
        translation.activate(language)
        request.LANGUAGE_CODE = language
