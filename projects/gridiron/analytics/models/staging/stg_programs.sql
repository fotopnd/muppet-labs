select
    p.id            as program_id,
    p.name,
    p.emoji,
    p.mascot,
    p.city,
    p.tier,
    p.prestige,
    p.elo,
    p.stadium_name,
    p.stadium_cap,
    p.founded_year,
    c.code          as conglomerate_code,
    c.full_name     as conglomerate_name,
    c.network,
    c.region
from {{ source('gridiron', 'programs') }} p
join {{ source('gridiron', 'conglomerates') }} c on c.id = p.conglomerate_id
