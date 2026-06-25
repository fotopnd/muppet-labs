select
    id                  as program_id,
    conglomerate_id,
    name                as program_name,
    emoji,
    mascot,
    city,
    tier,
    prestige,
    founded_year,
    primary_color,
    secondary_color,
    stadium_name,
    stadium_cap,
    elo,
    elo_seed_min,
    elo_seed_max,
    created_at
from {{ source('gridiron', 'programs') }}
