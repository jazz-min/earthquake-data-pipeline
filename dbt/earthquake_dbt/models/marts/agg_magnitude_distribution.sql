select
  magnitude,
  count(*) as freq
from {{ ref('stg_earthquakes') }}
group by magnitude
order by magnitude
