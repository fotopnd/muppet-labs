select
    id                  as conglomerate_id,
    code,
    full_name           as conglomerate_name,
    network,
    region,
    primary_color,
    secondary_color,
    tertiary_color,
    created_at
from {{ source('gridiron', 'conglomerates') }}
