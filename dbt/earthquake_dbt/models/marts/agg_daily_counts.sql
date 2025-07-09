--- for time-series earthquake counts

select
  date,
  count(*) as quake_count
from {{ref('stg_earthquakes')}}
group by date
order by date
