--- top 10 strongest

select *
from {{ ref('stg_earthquakes') }}
order by magnitude desc
limit 10
