select
  place,
  year_month,
  count(*) as quake_count
from {{ ref('stg_earthquakes') }}
group by place, year_month
