with stats   as (select * from {{ ref('stg_player_game_stats') }}),
     games   as (select game_id, season from {{ ref('stg_games') }}),
     players as (select * from {{ ref('stg_players') }})

select
    s.player_id,
    pl.full_name                                                                as player_name,
    pl.position,
    pl.program_name,
    pl.clutch,
    pl.rivalry_dna,
    g.season,

    count(*)                                                                    as games_played,

    sum(s.pass_yards)                                                           as pass_yards,
    sum(s.pass_tds)                                                             as pass_tds,
    sum(s.interceptions)                                                        as interceptions,
    sum(s.rush_yards)                                                           as rush_yards,
    sum(s.rush_tds)                                                             as rush_tds,
    sum(s.receiving_yards)                                                      as receiving_yards,
    sum(s.receiving_tds)                                                        as receiving_tds,
    sum(s.receptions)                                                           as receptions,
    sum(s.targets)                                                              as targets,
    sum(s.tackles)                                                              as tackles,
    sum(s.sacks)                                                                as sacks,
    sum(s.forced_fumbles)                                                       as forced_fumbles,
    sum(s.ints_def)                                                             as ints_def,

    round(sum(s.pass_yards)::numeric      / nullif(count(*), 0), 1)            as pass_yards_per_game,
    round(sum(s.rush_yards)::numeric      / nullif(count(*), 0), 1)            as rush_yards_per_game,
    round(sum(s.receiving_yards)::numeric / nullif(count(*), 0), 1)            as receiving_yards_per_game
from stats s
join games   g  on g.game_id   = s.game_id
join players pl on pl.player_id = s.player_id
group by s.player_id, pl.full_name, pl.position, pl.program_name, pl.clutch, pl.rivalry_dna, g.season
