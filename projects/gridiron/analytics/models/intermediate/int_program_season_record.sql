with outcomes as (select * from {{ ref('int_game_outcomes') }}),

home_games as (
    select
        home_program_id     as program_id,
        home_program_name   as program_name,
        home_conglomerate   as conglomerate_name,
        season,
        1                                                           as games_played,
        case when home_score > away_score then 1 else 0 end         as wins,
        case when home_score < away_score then 1 else 0 end         as losses,
        home_score                                                  as points_for,
        away_score                                                  as points_against
    from outcomes
),

away_games as (
    select
        away_program_id     as program_id,
        away_program_name   as program_name,
        away_conglomerate   as conglomerate_name,
        season,
        1                                                           as games_played,
        case when away_score > home_score then 1 else 0 end         as wins,
        case when away_score < home_score then 1 else 0 end         as losses,
        away_score                                                  as points_for,
        home_score                                                  as points_against
    from outcomes
)

select
    program_id,
    program_name,
    conglomerate_name,
    season,
    sum(games_played)                                                           as games_played,
    sum(wins)                                                                   as wins,
    sum(losses)                                                                 as losses,
    sum(points_for)                                                             as points_for,
    sum(points_against)                                                         as points_against,
    round(sum(points_for)::numeric    / nullif(sum(games_played), 0), 1)        as avg_points_for,
    round(sum(points_against)::numeric / nullif(sum(games_played), 0), 1)       as avg_points_against
from (select * from home_games union all select * from away_games) combined
group by program_id, program_name, conglomerate_name, season
