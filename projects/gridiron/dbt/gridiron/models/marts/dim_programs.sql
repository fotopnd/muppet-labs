select
    p.program_id,
    p.program_name,
    p.emoji,
    p.mascot,
    p.city,
    p.tier,
    p.prestige,
    p.founded_year,
    p.primary_color,
    p.secondary_color,
    p.stadium_name,
    p.stadium_cap,
    p.elo             as current_elo,
    c.conglomerate_id,
    c.code            as conglomerate_code,
    c.conglomerate_name,
    c.network,
    c.region
from {{ ref('stg_programs') }} p
left join {{ ref('stg_conglomerates') }} c using (conglomerate_id)
