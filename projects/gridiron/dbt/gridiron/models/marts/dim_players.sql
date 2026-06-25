select
    pl.player_id,
    pl.program_id,
    pr.program_name,
    pr.conglomerate_code,
    pl.full_name,
    pl.first_name,
    pl.last_name,
    pl.position,
    pl.position_group,
    pl.class,
    pl.year,
    pl.jersey_num,
    pl.overall_rating,
    pl.alpha,
    pl.delta,
    pl.sigma,
    pl.psi,
    pl.omega,
    pl.created_at
from {{ ref('stg_players') }} pl
left join {{ ref('dim_programs') }} pr using (program_id)
