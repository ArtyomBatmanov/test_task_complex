from django.shortcuts import render, redirect
from django.views.generic import FormView, TemplateView
from django.urls import reverse_lazy
import requests
import json
from .forms import CityForm
from django.http import JsonResponse

class IndexView(FormView):
    template_name = 'weather/index.html'
    form_class = CityForm
    success_url = reverse_lazy('index')

    def form_valid(self, form):
        city = form.cleaned_data['city']
        response = redirect('weather', city=city)
        search_history = self.request.COOKIES.get('search_history')
        if search_history:
            try:
                search_history = json.loads(search_history)
            except json.JSONDecodeError:
                search_history = []
        else:
            search_history = []

        if city not in search_history:
            search_history.append(city)
        response.set_cookie('search_history', json.dumps(search_history))
        return response

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        search_history = self.request.COOKIES.get('search_history')
        if search_history:
            try:
                context['search_history'] = json.loads(search_history)
            except json.JSONDecodeError:
                context['search_history'] = []
        else:
            context['search_history'] = []
        return context

class WeatherView(TemplateView):
    template_name = 'weather/weather.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        city = self.kwargs.get('city')
        weather_data = self.get_weather(city)
        context['city'] = city
        context['weather'] = weather_data
        return context

    def get_weather(self, city):
        coordinates = self.get_coordinates(city)
        if not coordinates:
            return None
        try:
            response = requests.get(
                'https://api.open-meteo.com/v1/forecast',
                params={
                    'latitude': coordinates['latitude'],
                    'longitude': coordinates['longitude'],
                    'current_weather': 'true',
                    'hourly': 'temperature_2m,relative_humidity_2m,wind_speed_10m'
                }
            )
            response.raise_for_status()
            data = response.json()
            hourly_data = [
                {
                    'time': time,
                    'temperature': temperature,
                    'humidity': humidity,
                    'wind_speed': wind_speed
                }
                for time, temperature, humidity, wind_speed in zip(
                    data['hourly']['time'],
                    data['hourly']['temperature_2m'],
                    data['hourly']['relative_humidity_2m'],
                    data['hourly']['wind_speed_10m']
                )
            ]
            return {
                'current': data['current_weather'],
                'hourly': hourly_data
            }
        except requests.RequestException as e:
            print(f"Error fetching weather data: {e}")
            return None

    def get_coordinates(self, city):
        try:
            url = 'https://nominatim.openstreetmap.org/search'
            params = {
                'q': city,
                'format': 'json',
                'limit': 1
            }
            response = requests.get(url, params=params)
            response.raise_for_status()
            data = response.json()
            if data:
                return {
                    'latitude': data[0]['lat'],
                    'longitude': data[0]['lon']
                }
            return None
        except requests.RequestException as e:
            print(f"Error fetching coordinates: {e}")
            return None

def city_autocomplete(request):
    if 'term' in request.GET:
        search_term = request.GET.get('term')
        url = 'https://nominatim.openstreetmap.org/search'
        params = {
            'q': search_term,
            'format': 'json',
            'addressdetails': 1,
            'limit': 10
        }
        response = requests.get(url, params=params)
        results = response.json()
        cities = [{'label': result['display_name'], 'value': result['display_name']}
                  for result in results]
        return JsonResponse(cities, safe=False)
    return JsonResponse([], safe=False)
