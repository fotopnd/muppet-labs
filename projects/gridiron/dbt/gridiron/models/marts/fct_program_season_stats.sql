-- One row per program per season: W-L, points, ELO movement
with home_games as (
    select
        season,
        home_program_id     as program_id,
        home_score          as points_for,
        away_score          as points_against,
        case when winner_program_id = home_program_id then 1 else 0 end as win,
        case when loser_program_id  = home_program_id then 1 else 0 end as loss,
        home_elo_pre        as elo_pre,
        home_elo_post       as elo_post
    from {{ ref('fct_game_results') }}
    where not is_postseason
),

away_games as (
    select
        season,
        away_program_id     as program_id,
        away_score          as points_for,
        home_score          as points_against,
        case when winner_program_id = away_program_id then 1 else 0 end as win,
        case when loser_program_id  = away_program_id then 1 else 0 end as loss,
        away_elo_pre        as elo_pre,
        away_elo_post       as elo_post
    from {{ ref('fct_game_results') }}
    where not is_postseason
),

all_games as (
    select * from home_games
    union all
    select * from away_games
)

select
    a.season,
    a.program_id,
    p.program_name,
    p.conglomerate_code,
    p.tier,
    p.prestige,
    sum(a.win)                                      as wins,
    sum(a.loss)                                     as losses,
    sum(a.win) + sum(a.loss)                        as games_played,
    sum(a.points_for)                               as points_for,
    sum(a.points_against)                           as points_against,
    sum(a.points_for) - sum(a.points_against)       as point_differential,
    round(avg(a.points_for)::numeric, 1)            as avg_points_for,
    min(a.elo_pre)                                  as season_elo_start,
    max(a.elo_post)                                 as season_elo_end,
    round((max(a.elo_post) - min(a.elo_pre))::numeric, 1) as season_elo_delta
from all_games a
left join {{ ref('dim_programs') }} p using (program_id)
group by a.season, a.program_id, p.program_name, p.conglomerate_code, p.tier, p.prestige
order by a.season, wins desc
