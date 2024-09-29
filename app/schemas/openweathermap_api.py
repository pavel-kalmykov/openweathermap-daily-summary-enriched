from typing import Annotated

from pydantic import BaseModel, Field


class CloudCover(BaseModel):
    afternoon: Annotated[float, Field(description="Afternoon cloud cover percentage")]


class Humidity(BaseModel):
    afternoon: Annotated[float, Field(description="Afternoon humidity percentage")]


class Precipitation(BaseModel):
    total: Annotated[float, Field(description="Total precipitation in mm")]


class Temperature(BaseModel):
    min: Annotated[
        float, Field(description="Minimum temperature (in Kelvin by default)")
    ]
    max: Annotated[
        float, Field(description="Maximum temperature (in Kelvin by default)")
    ]
    afternoon: Annotated[
        float, Field(description="Afternoon temperature (in Kelvin by default)")
    ]
    night: Annotated[
        float, Field(description="Night temperature (in Kelvin by default)")
    ]
    evening: Annotated[
        float, Field(description="Evening temperature (in Kelvin by default)")
    ]
    morning: Annotated[
        float, Field(description="Morning temperature (in Kelvin by default)")
    ]


class Pressure(BaseModel):
    afternoon: Annotated[
        float, Field(description="Afternoon atmospheric pressure in hPa")
    ]


class Max(BaseModel):
    speed: Annotated[float, Field(description="Maximum wind speed in m/s")]
    direction: Annotated[
        float, Field(description="Direction of maximum wind in degrees")
    ]


class Wind(BaseModel):
    max: Annotated[Max, Field(description="Maximum wind information")]


class WeatherDailySummaryResult(BaseModel):
    lat: Annotated[float, Field(description="Latitude of the location")]
    lon: Annotated[float, Field(description="Longitude of the location")]
    tz: Annotated[str, Field(description="Timezone of the location")]
    date: Annotated[str, Field(description="Date of the weather summary (YYYY-MM-DD)")]
    units: Annotated[str, Field(description="Units used for measurements")]
    cloud_cover: Annotated[CloudCover, Field(description="Cloud cover information")]
    humidity: Annotated[Humidity, Field(description="Humidity information")]
    precipitation: Annotated[
        Precipitation, Field(description="Precipitation information")
    ]
    temperature: Annotated[Temperature, Field(description="Temperature information")]
    pressure: Annotated[Pressure, Field(description="Pressure information")]
    wind: Annotated[Wind, Field(description="Wind information")]


class GeocodingResult(BaseModel):
    name: Annotated[str, Field(description="Name of the location")]
    local_names: Annotated[
        dict[str, str] | None,
        Field(None, description="Names of the location in different languages"),
    ]
    lat: Annotated[float, Field(description="Latitude of the location")]
    lon: Annotated[float, Field(description="Longitude of the location")]
    country: Annotated[str | None, Field(None, description="Country of the location")]
    state: Annotated[
        str | None, Field(None, description="State or region of the location")
    ]
