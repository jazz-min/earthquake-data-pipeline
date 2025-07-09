select
  place,
  round(avg(depth_km)::numeric, 2)  as avg_depth_km
from {{ ref('stg_earthquakes') }}
group by place
order by avg_depth_km desc
