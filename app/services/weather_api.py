"""
OpenWeatherMap client wrapper with demo/fallback behavior.

Provides a small helper to compute a forecast-based premium adjustment
between -0.15 and +0.15 (±15%). If `OPENWEATHER_API_KEY` is set, it
will try a lightweight API call; otherwise it uses deterministic mock data.
"""
import os
import requests
from datetime import datetime


class OpenWeatherMapClient:
    def __init__(self, api_key: str | None = None):
        self.api_key = api_key or os.environ.get('OPENWEATHER_API_KEY')
        self.session = requests.Session()

    def get_current_weather(self, city: str):
        """Return a simple current weather dict: temp, humidity, rain_mm"""
        if not self.api_key:
            return self._mock_current_weather(city)

        try:
            url = 'https://api.openweathermap.org/data/2.5/weather'
            params = {'q': city, 'appid': self.api_key, 'units': 'metric'}
            r = self.session.get(url, params=params, timeout=5)
            r.raise_for_status()
            data = r.json()
            temp = data.get('main', {}).get('temp')
            humidity = data.get('main', {}).get('humidity')
            rain_mm = 0.0
            if 'rain' in data and isinstance(data['rain'], dict):
                rain_mm = data['rain'].get('1h', 0.0) or data['rain'].get('3h', 0.0) or 0.0
            return {'temp': temp, 'humidity': humidity, 'rain_mm': rain_mm}
        except Exception:
            return self._mock_current_weather(city)

    def get_forecast(self, city: str, days: int = 7):
        """Return a simplified forecast summary.
        If API key is available, attempt to call OWM forecast; else fallback.
        """
        if not self.api_key:
            return self._mock_forecast(city, days)

        try:
            # Use 5 day / 3hr forecast endpoint as simple option
            url = 'https://api.openweathermap.org/data/2.5/forecast'
            params = {'q': city, 'appid': self.api_key, 'units': 'metric'}
            r = self.session.get(url, params=params, timeout=6)
            r.raise_for_status()
            data = r.json()
            # Aggregate rainfall and high temp probability
            high_temp_events = 0
            heavy_rain_events = 0
            total_points = 0
            for entry in data.get('list', []):
                total_points += 1
                temp = entry.get('main', {}).get('temp', 0)
                rain = 0.0
                if 'rain' in entry and isinstance(entry['rain'], dict):
                    rain = entry['rain'].get('3h', 0.0) or 0.0
                if temp and temp >= 42:
                    high_temp_events += 1
                if rain and rain >= 50:
                    heavy_rain_events += 1

            return {'points': total_points, 'high_temp_events': high_temp_events, 'heavy_rain_events': heavy_rain_events}
        except Exception:
            return self._mock_forecast(city, days)

    def get_forecast_adjustment_pct(self, city: str) -> float:
        """Compute forecast adjustment percentage in [-0.15, 0.15].
        Positive means increase premium; negative means decrease.
        """
        # If API key present, use real data heuristics
        if self.api_key:
            f = self.get_forecast(city, days=7)
            pts = f.get('points', 0) or 1
            high = f.get('high_temp_events', 0)
            heavy = f.get('heavy_rain_events', 0)
            score = 0.0
            if high / pts > 0.05:
                score += 0.12
            if heavy / pts > 0.03:
                score += 0.12
            return max(-0.15, min(0.15, score))

        # Fallback deterministic mapping for demo
        city = city.lower() if city else ''
        if 'mumbai' in city or 'chennai' in city or 'kolkata' in city:
            return 0.12  # monsoon / coastal rain risk
        if 'delhi' in city or 'jaipur' in city:
            return 0.10  # heat risk
        if 'pune' in city or 'bengaluru' in city or 'bangalore' in city:
            return 0.02  # mild
        return 0.0

    def _mock_current_weather(self, city: str):
        city = city.lower() if city else ''
        if 'mumbai' in city:
            return {'temp': 29, 'humidity': 85, 'rain_mm': 2}
        if 'delhi' in city:
            return {'temp': 38, 'humidity': 30, 'rain_mm': 0}
        if 'bangalore' in city or 'bengaluru' in city:
            return {'temp': 26, 'humidity': 65, 'rain_mm': 0}
        return {'temp': 30, 'humidity': 50, 'rain_mm': 0}

    def _mock_forecast(self, city: str, days: int = 7):
        city = city.lower() if city else ''
        if 'mumbai' in city:
            return {'points': days, 'high_temp_events': 0, 'heavy_rain_events': max(1, days // 3)}
        if 'delhi' in city:
            return {'points': days, 'high_temp_events': max(1, days // 4), 'heavy_rain_events': 0}
        return {'points': days, 'high_temp_events': 0, 'heavy_rain_events': 0}
"""
OpenWeatherMap API Integration
Fetches real weather data for risk assessment
Author: Member 1
"""

import requests
import os
from datetime import datetime

class OpenWeatherMapClient:
    """
    Fetches real-time weather data
    Free tier: 60 calls/minute, enough for demo
    """
    
    def __init__(self):
        # Get API key from environment variable
        # Sign up free at https://openweathermap.org/api
        self.api_key = os.environ.get('OPENWEATHER_API_KEY', 'demo_key')
        self.use_mock = self.api_key == 'demo_key'
        
        if self.use_mock:
            print("⚠️ Using mock weather data. Set OPENWEATHER_API_KEY for real data.")
    
    def get_current_weather(self, city):
        """
        Get current temperature and conditions
        """
        if self.use_mock:
            return self._mock_weather(city)
        
        try:
            url = "http://api.openweathermap.org/data/2.5/weather"
            params = {
                'q': city,
                'appid': self.api_key,
                'units': 'metric'  # Celsius
            }
            response = requests.get(url, params=params)
            data = response.json()
            
            return {
                "temperature": data['main']['temp'],
                "humidity": data['main']['humidity'],
                "rain": data.get('rain', {}).get('1h', 0),
                "condition": data['weather'][0]['description'],
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            print(f"Weather API error: {e}")
            return self._mock_weather(city)
    
    def get_forecast(self, city, days=7):
        """
        Get weather forecast for next N days
        """
        if self.use_mock:
            return self._mock_forecast(city, days)
        
        try:
            url = "http://api.openweathermap.org/data/2.5/forecast"
            params = {
                'q': city,
                'appid': self.api_key,
                'units': 'metric'
            }
            response = requests.get(url, params=params)
            data = response.json()
            
            forecast = []
            for item in data['list'][:days*8]:  # 3-hour intervals
                forecast.append({
                    "datetime": item['dt_txt'],
                    "temp_max": item['main']['temp_max'],
                    "temp_min": item['main']['temp_min'],
                    "rain": item.get('rain', {}).get('3h', 0),
                    "condition": item['weather'][0]['description']
                })
            
            return forecast
        except Exception as e:
            print(f"Forecast API error: {e}")
            return self._mock_forecast(city, days)
    
    def _mock_weather(self, city):
        """Mock data for demo when API key not available"""
        mock_data = {
            'Mumbai': {'temperature': 32, 'humidity': 75, 'rain': 0, 'condition': 'haze'},
            'Delhi': {'temperature': 38, 'humidity': 45, 'rain': 0, 'condition': 'sunny'},
            'Bangalore': {'temperature': 28, 'humidity': 65, 'rain': 0, 'condition': 'clouds'},
            'Chennai': {'temperature': 34, 'humidity': 70, 'rain': 0, 'condition': 'sunny'},
            'Kolkata': {'temperature': 33, 'humidity': 72, 'rain': 0, 'condition': 'haze'}
        }
        return mock_data.get(city, {'temperature': 30, 'humidity': 60, 'rain': 0, 'condition': 'clear'})
    
    def _mock_forecast(self, city, days):
        """Mock forecast for demo"""
        forecast = []
        for i in range(days):
            forecast.append({
                "datetime": f"2026-04-{i+1:02d} 12:00:00",
                "temp_max": 35 - i,
                "temp_min": 25 - i,
                "rain": 10 if i == 2 else 0,
                "condition": "rain" if i == 2 else "clear"
            })
        return forecast
    
    def is_heat_wave(self, city):
        """Check if heat wave conditions exist (>42°C)"""
        weather = self.get_current_weather(city)
        return weather['temperature'] > 42
    
    def is_heavy_rain(self, city):
        """Check if heavy rain conditions exist (>50mm)"""
        weather = self.get_current_weather(city)
        return weather['rain'] > 50


weather_client = OpenWeatherMapClient()