select
    id                  as game_id,
    season,
    week,
    home_program_id,
    away_program_id,
    status,
    home_score,
    away_score,
    is_rivalry,
    is_postseason,
    elo_tiebreak,
    broadcast_slot,
    home_elo_pre,
    away_elo_pre,
    home_elo_post,
    away_elo_post,
    -- derived
    case
        when status = 'complete' and home_score > away_score then home_program_id
        when status = 'complete' and away_score > home_score then away_program_id
    end                 as winner_program_id,
    case
        when status = 'complete' and home_score > away_score then away_program_id
        when status = 'complete' and away_score > home_score then home_program_id
    end                 as loser_program_id,
    case
        when status = 'complete'
        then abs(home_score - away_score)
    end                 as margin,
    scheduled_at,
    started_at,
    ended_at,
    replay_started_at,
    created_at
from {{ source('gridiron', 'games') }}
