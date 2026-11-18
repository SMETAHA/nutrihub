from django.conf import settings
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse


class LanguageSwitchTests(TestCase):
    def test_english_is_default_even_when_browser_prefers_russian(self):
        response = self.client.get('/', HTTP_ACCEPT_LANGUAGE='ru')

        self.assertContains(response, 'Track your nutrition. Reach your goals.')
        self.assertContains(response, '<html lang="en"')

    def test_language_button_persists_russian_choice(self):
        response = self.client.post(
            reverse('set_language'),
            {'language': 'ru', 'next': '/'},
        )

        self.assertEqual(response.status_code, 302)
        response = self.client.get('/')

        self.assertContains(response, 'Следите за питанием')
        self.assertContains(response, '<html lang="ru"')

    def test_planner_macro_preview_uses_selected_language(self):
        user = get_user_model().objects.create_user(
            username='language-user',
            password='test-password',
        )
        self.client.force_login(user)
        self.client.cookies[settings.LANGUAGE_COOKIE_NAME] = 'ru'

        response = self.client.get(reverse('planner_view'))

        self.assertContains(response, 'data-kcal-label="ккал"')
        self.assertContains(response, 'data-protein-label="Белки"')
