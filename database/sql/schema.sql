DROP TABLE IF EXISTS weather_observations CASCADE;
DROP TABLE IF EXISTS energy_generation   CASCADE;
DROP TABLE IF EXISTS energy_demand       CASCADE;
DROP TABLE IF EXISTS generation_sources  CASCADE;
DROP TABLE IF EXISTS cities              CASCADE;

CREATE TABLE cities (
    city_id    SERIAL       PRIMARY KEY,
    city_name  VARCHAR(50)  UNIQUE NOT NULL,
    latitude   NUMERIC(8, 5),
    longitude  NUMERIC(8, 5)
);

CREATE TABLE generation_sources (
    source_id     SERIAL      PRIMARY KEY,
    source_name   VARCHAR(60) UNIQUE NOT NULL,
    is_renewable  BOOLEAN     NOT NULL DEFAULT FALSE
);

CREATE TABLE energy_demand (
    ts                 TIMESTAMPTZ    PRIMARY KEY,
    total_load_actual  NUMERIC(10, 2) NOT NULL,
    price_actual       NUMERIC(10, 2),
    price_day_ahead    NUMERIC(10, 2)
);

CREATE TABLE energy_generation (
    ts             TIMESTAMPTZ  NOT NULL REFERENCES energy_demand (ts) ON DELETE CASCADE,
    source_id      INT          NOT NULL REFERENCES generation_sources (source_id),
    generation_mw  NUMERIC(10, 2),
    PRIMARY KEY (ts, source_id)
);

CREATE TABLE weather_observations (
    ts          TIMESTAMPTZ  NOT NULL REFERENCES energy_demand (ts) ON DELETE CASCADE,
    city_id     INT          NOT NULL REFERENCES cities (city_id),
    temp        NUMERIC(6, 2),
    pressure    NUMERIC(7, 2),
    humidity    NUMERIC(5, 1),
    wind_speed  NUMERIC(6, 2),
    clouds_all  NUMERIC(5, 1),
    PRIMARY KEY (ts, city_id)
);

CREATE INDEX idx_generation_source ON energy_generation   (source_id);
CREATE INDEX idx_weather_city      ON weather_observations (city_id);
CREATE INDEX idx_weather_ts        ON weather_observations (ts);
CREATE INDEX idx_generation_ts     ON energy_generation    (ts);
