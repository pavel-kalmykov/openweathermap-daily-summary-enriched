from typing import Self

import polars as pl


class WeatherDataProcessor:
    def process_data(self: Self, raw_data: list[dict]) -> pl.DataFrame:
        # Convert the raw data to a Polars DataFrame
        weather_df = pl.DataFrame(raw_data)

        # Flatten nested structures
        weather_df = weather_df.with_columns(
            [
                pl.col("lat").alias("latitude"),
                pl.col("lon").alias("longitude"),
                pl.col("tz").alias("timezone"),
                pl.col("date").str.strptime(pl.Date, format="%Y-%m-%d").alias("date"),
                pl.col("cloud_cover")
                .struct.field("afternoon")
                .alias("cloud_cover_afternoon"),
                pl.col("humidity")
                .struct.field("afternoon")
                .alias("humidity_afternoon"),
                pl.col("precipitation")
                .struct.field("total")
                .alias("precipitation_total"),
                pl.col("temperature").struct.field("min").alias("temp_min"),
                pl.col("temperature").struct.field("max").alias("temp_max"),
                pl.col("temperature").struct.field("afternoon").alias("temp_afternoon"),
                pl.col("temperature").struct.field("night").alias("temp_night"),
                pl.col("temperature").struct.field("evening").alias("temp_evening"),
                pl.col("temperature").struct.field("morning").alias("temp_morning"),
                pl.col("pressure")
                .struct.field("afternoon")
                .alias("pressure_afternoon"),
                pl.col("wind")
                .struct.field("max")
                .struct.field("speed")
                .alias("wind_speed_max"),
                pl.col("wind")
                .struct.field("max")
                .struct.field("direction")
                .alias("wind_direction_max"),
            ]
        )

        # Drop original nested columns
        weather_df = weather_df.drop(
            [
                "lat",
                "lon",
                "tz",
                "units",
                "cloud_cover",
                "humidity",
                "precipitation",
                "temperature",
                "pressure",
                "wind",
            ]
        )

        # Enrichment operations
        weather_df = self._add_temperature_variability_index(weather_df)
        weather_df = self._add_seasonal_classification(weather_df)
        weather_df = self._add_extreme_weather_detection(weather_df)
        weather_df = self._add_humidex(weather_df)
        weather_df = self._add_precipitation_intensity(weather_df)
        weather_df = self._add_wind_chill(weather_df)
        weather_df = self._add_heat_index(weather_df)

        return weather_df

    def _add_temperature_variability_index(
        self: Self, df: pl.DataFrame
    ) -> pl.DataFrame:
        return df.with_columns(
            [
                (pl.col("temp_max") - pl.col("temp_min")).alias("temp_range"),
                ((pl.col("temp_max") - pl.col("temp_min")) / pl.col("temp_max")).alias(
                    "temp_variability_index"
                ),
            ]
        )

    def _add_seasonal_classification(self: Self, df: pl.DataFrame) -> pl.DataFrame:
        return df.with_columns(
            [
                pl.when(pl.col("temp_afternoon") >= 303.15)
                .then(pl.lit("Summer"))
                .when(
                    (pl.col("temp_afternoon") >= 293.15)
                    & (pl.col("temp_afternoon") < 303.15)
                )
                .then(pl.lit("Late Spring/Early Fall"))
                .when(
                    (pl.col("temp_afternoon") >= 283.15)
                    & (pl.col("temp_afternoon") < 293.15)
                )
                .then(pl.lit("Spring/Fall"))
                .otherwise(pl.lit("Winter"))
                .alias("season")
            ]
        )

    def _add_extreme_weather_detection(self: Self, df: pl.DataFrame) -> pl.DataFrame:
        return df.with_columns(
            [
                ((pl.col("temp_max") >= 308.15) | (pl.col("temp_min") < 263.15)).alias(
                    "extreme_temperature"
                ),
                (pl.col("precipitation_total") > 50).alias("extreme_precipitation"),
                (pl.col("wind_speed_max") > 20).alias("extreme_wind"),
            ]
        )

    def _add_humidex(self: Self, df: pl.DataFrame) -> pl.DataFrame:
        # https://www.ohcow.on.ca/edit/files/general_handouts/heat-stress-calculator.html
        # Convert temperature from Kelvin to Celsius
        temp_c = pl.col("temp_afternoon") - 273.15

        # Calculate dewpoint
        dewpoint = (
            (pl.col("humidity_afternoon") / 100) ** (1 / 8) * (112 + 0.9 * temp_c)
            + 0.1 * temp_c
            - 112
        )

        # Calculate humidex
        humidex = temp_c + 0.5555 * (
            6.11 * 10 ** (7.5 * dewpoint / (237.7 + dewpoint)) - 10
        )

        return df.with_columns(
            [
                (humidex + 273.15).alias("humidex")  # Convert back to Kelvin
            ]
        )

    def _add_precipitation_intensity(self: Self, df: pl.DataFrame) -> pl.DataFrame:
        return df.with_columns(
            [
                pl.when(pl.col("precipitation_total") == 0)
                .then(pl.lit("None"))
                .when(pl.col("precipitation_total") < 10)
                .then(pl.lit("Light"))
                .when(pl.col("precipitation_total") < 50)
                .then(pl.lit("Moderate"))
                .otherwise(pl.lit("Heavy"))
                .alias("precipitation_intensity")
            ]
        )

    def _add_wind_chill(self: Self, df: pl.DataFrame) -> pl.DataFrame:
        # http://weather.uky.edu/aen599/wchart.htm
        # https://www.weather.gov/epz/wxcalc_windchill
        temp_k = pl.col("temp_afternoon")
        wind_speed = pl.col("wind_speed_max")

        wind_chill = 306.15 - (
            0.453843 * wind_speed.sqrt() + 0.464255 - 0.0453843 * wind_speed
        ) * (306.15 - temp_k)

        # Wind chill is only applicable when temperature is at or below 10°C (283.15K)
        # and wind speed is above 4.8 km/h (1.33 m/s)
        wind_chill_applicable = (temp_k <= 283.15) & (wind_speed > 1.33)

        return df.with_columns(
            [
                pl.when(wind_chill_applicable)
                .then(wind_chill)
                .otherwise(None)
                .alias("wind_chill")
            ]
        )

    def _add_heat_index(self: Self, df: pl.DataFrame) -> pl.DataFrame:
        # https://www.wpc.ncep.noaa.gov/html/heatindex_equation.shtml
        # https://www.wpc.ncep.noaa.gov/html/heatindex.shtml
        # Convert temperature from Kelvin to Fahrenheit
        temp_f = (pl.col("temp_afternoon") - 273.15) * 9 / 5 + 32
        rel_hum = pl.col("humidity_afternoon")

        # Simple formula for low heat index values
        hi_simple = 0.5 * (temp_f + 61.0 + ((temp_f - 68.0) * 1.2) + (rel_hum * 0.094))

        # Rothfusz regression
        hi = (
            -42.379
            + 2.04901523 * temp_f
            + 10.14333127 * rel_hum
            - 0.22475541 * temp_f * rel_hum
            - 0.00683783 * temp_f * temp_f
            - 0.05481717 * rel_hum * rel_hum
            + 0.00122874 * temp_f * temp_f * rel_hum
            + 0.00085282 * temp_f * rel_hum * rel_hum
            - 0.00000199 * temp_f * temp_f * rel_hum * rel_hum
        )

        # Adjustments
        adjustment = (
            pl.when((rel_hum < 13) & (temp_f >= 80) & (temp_f <= 112))
            .then(((13 - rel_hum) / 4) * ((17 - abs(temp_f - 95)) / 17).sqrt())
            .when((rel_hum > 85) & (temp_f >= 80) & (temp_f <= 87))
            .then(((rel_hum - 85) / 10) * ((87 - temp_f) / 5))
            .otherwise(0)
        )

        hi_adjusted = pl.when(hi_simple < 80).then(hi_simple).otherwise(hi + adjustment)

        # Convert back to Kelvin
        hi_kelvin = (hi_adjusted - 32) * 5 / 9 + 273.15

        return df.with_columns([hi_kelvin.alias("heat_index")])
