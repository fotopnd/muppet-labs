with games as (
    select * from {{ ref('stg_games') }}
    where status = 'complete'
),

home as (select program_id, program_name, conglomerate_code, current_elo from {{ ref('dim_programs') }}),
away as (select program_id, program_name, conglomerate_code, current_elo from {{ ref('dim_programs') }})

select
    g.game_id,
    g.season,
    g.week,
    g.is_rivalry,
    g.is_postseason,
    g.broadcast_slot,

    g.home_program_id,
    h.program_name      as home_program_name,
    h.conglomerate_code as home_conglomerate,
    g.home_score,
    g.home_elo_pre,
    g.home_elo_post,
    round((g.home_elo_post - g.home_elo_pre)::numeric, 1) as home_elo_delta,

    g.away_program_id,
    a.program_name      as away_program_name,
    a.conglomerate_code as away_conglomerate,
    g.away_score,
    g.away_elo_pre,
    g.away_elo_post,
    round((g.away_elo_post - g.away_elo_pre)::numeric, 1) as away_elo_delta,

    g.winner_program_id,
    g.loser_program_id,
    g.margin,

    -- upset: lower pre-game ELO team won
    case
        when g.home_elo_pre < g.away_elo_pre and g.winner_program_id = g.home_program_id then true
        when g.away_elo_pre < g.home_elo_pre and g.winner_program_id = g.away_program_id then true
        else false
    end as is_upset,

    g.started_at,
    g.ended_at
from games g
left join home h on h.program_id = g.home_program_id
left join away a on a.program_id = g.away_program_id
