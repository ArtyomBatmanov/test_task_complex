from django.test import TestCase
from django.urls import reverse

class WeatherAppTests(TestCase):
    def test_index_page(self):
        response = self.client.get(reverse('index'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'weather/index.html')

    def test_weather_page(self):
        response = self.client.get(reverse('weather', args=['Tokyo']))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'weather/weather.html')
