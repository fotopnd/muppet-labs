with records  as (select * from {{ ref('int_program_season_record') }}),
     programs as (select * from {{ ref('stg_programs') }})

select
    r.program_id,
    r.program_name,
    p.emoji,
    r.conglomerate_name,
    p.tier,
    p.prestige,
    p.elo,
    r.season,
    r.wins,
    r.losses,
    r.games_played,
    r.points_for,
    r.points_against,
    r.avg_points_for,
    r.avg_points_against,
    r.points_for - r.points_against                                             as point_differential,
    rank() over (
        partition by r.conglomerate_name, r.season
        order by r.wins desc, r.losses asc, p.elo desc
    )                                                                           as conference_rank
from records r
join programs p on p.program_id = r.program_id
