with games    as (select * from {{ ref('stg_games') }}),
     home_prg as (select * from {{ ref('stg_programs') }}),
     away_prg as (select * from {{ ref('stg_programs') }})

select
    g.game_id,
    g.season,
    g.week,
    g.is_rivalry,
    g.is_postseason,
    g.broadcast_slot,

    g.home_program_id,
    h.name              as home_program_name,
    h.conglomerate_name as home_conglomerate,

    g.away_program_id,
    a.name              as away_program_name,
    a.conglomerate_name as away_conglomerate,

    g.home_score,
    g.away_score,
    g.home_score - g.away_score                                     as margin,

    case
        when g.home_score > g.away_score then g.home_program_id
        when g.away_score > g.home_score then g.away_program_id
    end                                                             as winner_program_id,
    case
        when g.home_score > g.away_score then h.name
        when g.away_score > g.home_score then a.name
    end                                                             as winner_name,

    g.home_elo_pre,
    g.away_elo_pre,
    g.home_elo_post,
    g.away_elo_post,
    coalesce(g.home_elo_post, g.home_elo_pre) - g.home_elo_pre     as home_elo_delta,
    coalesce(g.away_elo_post, g.away_elo_pre) - g.away_elo_pre     as away_elo_delta,

    g.ended_at
from games g
join home_prg h on h.program_id = g.home_program_id
join away_prg a on a.program_id = g.away_program_id
