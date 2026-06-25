select
    id              as player_id,
    program_id,
    first_name,
    last_name,
    first_name || ' ' || last_name  as full_name,
    position,
    case
        when position = 'QB'                            then 'QB'
        when position in ('RB', 'FB')                  then 'RB'
        when position in ('WR', 'TE')                  then 'WR'
        when position in ('LT', 'LG', 'C', 'RG', 'RT') then 'OL'
        when position in ('DT', 'DE')                  then 'DL'
        when position in ('LOLB', 'ROLB', 'MLB')       then 'LB'
        when position in ('CB', 'SS', 'FS', 'DB')      then 'DB'
        when position in ('K', 'P')                    then 'ST'
        else 'OTHER'
    end             as position_group,
    year,
    case year
        when 1 then 'FR'
        when 2 then 'SO'
        when 3 then 'JR'
        when 4 then 'SR'
    end             as class,
    jersey_num,
    alpha,
    delta,
    sigma,
    psi,
    omega,
    -- composite rating: simple average of the five attributes
    round(((alpha + delta + sigma + psi + omega) / 5.0)::numeric, 3) as overall_rating,
    created_at
from {{ source('gridiron', 'players') }}
