select
    id,
    game_id,
    player_id,
    program_id,
    pass_attempts,
    pass_completions,
    pass_yards,
    pass_tds,
    interceptions,
    rush_attempts,
    rush_yards,
    rush_tds,
    targets,
    receptions,
    receiving_yards,
    receiving_tds,
    tackles,
    sacks,
    forced_fumbles,
    ints_def,
    fg_attempts,
    fg_made,
    case when pass_attempts > 0
        then round(pass_completions::numeric / pass_attempts, 3)
        else null
    end as completion_pct,
    case when fg_attempts > 0
        then round(fg_made::numeric / fg_attempts, 3)
        else null
    end as fg_pct
from {{ source('gridiron', 'player_game_stats') }}
