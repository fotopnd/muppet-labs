select
    pl.id                                       as player_id,
    pl.program_id,
    pl.first_name || ' ' || pl.last_name        as full_name,
    pl.position,
    pl.year                                     as class_year,
    pl.jersey_num,
    pl.alpha                                    as clutch,
    pl.delta                                    as upside,
    pl.sigma                                    as consistency,
    pl.psi                                      as leadership,
    pl.omega                                    as rivalry_dna,
    p.name                                      as program_name,
    p.conglomerate_id
from {{ source('gridiron', 'players') }} pl
join {{ source('gridiron', 'programs') }} p on p.id = pl.program_id
