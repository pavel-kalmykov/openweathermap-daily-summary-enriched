# Weather Endpoints

## Get Enriched Weather Data

```http
GET /weather/enriched-day-summary
```

Retrieve enriched weather data for a specific location and date range.

### Query Parameters

| Parameter  | Type     | Description                                    |
|------------|----------|------------------------------------------------|
| start_date | date     | Start date for weather data (YYYY-MM-DD)       |
| end_date   | date     | End date for weather data (YYYY-MM-DD)         |
| latitude   | float    | Latitude of the location (optional)            |
| longitude  | float    | Longitude of the location (optional)           |
| location   | string   | Name of the location (optional)                |

**Note**: Provide either `latitude` and `longitude` OR `location`, not both.

### Response

```json
{
  "weather_data": [
    {
      "date": "2024-09-27",
      "latitude": 38.2653,
      "longitude": -0.6988,
      "timezone": "+02:00",
      "temp_min": 296.38,
      "temp_max": 302.46,
      "temp_afternoon": 300.86,
      "temp_night": 299.57,
      "temp_evening": 299.95,
      "temp_morning": 297.28,
      "temp_range": 6.08,
      "cloud_cover_afternoon": 0.0,
      "humidity_afternoon": 50.0,
      "precipitation_total": 0.0,
      "pressure_afternoon": 1014.0,
      "wind_speed_max": 8.23,
      "wind_direction_max": 310.0,
      "temp_variability_index": 0.02,
      "season": "Summer",
      "extreme_temperature": false,
      "extreme_precipitation": false,
      "extreme_wind": false,
      "humidex": 305.86,
      "precipitation_intensity": "None"
    }
  ],
  "errors": [],
  "geocoding_results": []
}
```

For more details on the response fields, please refer to the API source code and schemas.
