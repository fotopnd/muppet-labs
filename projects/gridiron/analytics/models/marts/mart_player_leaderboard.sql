select
    player_id,
    player_name,
    position,
    program_name,
    season,
    games_played,

    pass_yards,
    pass_tds,
    interceptions,
    rush_yards,
    rush_tds,
    receiving_yards,
    receiving_tds,
    receptions,
    targets,
    tackles,
    sacks,
    forced_fumbles,
    ints_def,

    pass_yards_per_game,
    rush_yards_per_game,
    receiving_yards_per_game,

    clutch,
    rivalry_dna,

    rank() over (partition by season order by pass_yards desc)          as pass_yards_rank,
    rank() over (partition by season order by rush_yards desc)          as rush_yards_rank,
    rank() over (partition by season order by receiving_yards desc)     as receiving_yards_rank,
    rank() over (partition by season order by tackles desc)             as tackles_rank,
    rank() over (partition by season order by sacks desc)               as sacks_rank
from {{ ref('int_player_season_stats') }}
