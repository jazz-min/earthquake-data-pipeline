--- staging cleaned data from raw

with source as (
  select * from raw_data.raw_earthquakes
),
renamed as (
  select
    id,
    time,
    to_char(time, 'YYYY-MM-DD') as date,
    to_char(time, 'YYYY-MM') as year_month,
    extract(hour from time) as hour,
    place,
    magnitude,
    latitude,
    longitude,
    depth_km,
    url
  from source
  where magnitude is not null
)

select * from renamed
