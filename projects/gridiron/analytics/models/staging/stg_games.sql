select
    id                  as game_id,
    season,
    week,
    home_program_id,
    away_program_id,
    is_rivalry,
    is_postseason,
    broadcast_slot,
    status,
    home_score,
    away_score,
    home_elo_pre,
    away_elo_pre,
    home_elo_post,
    away_elo_post,
    scheduled_at,
    started_at,
    ended_at
from {{ source('gridiron', 'games') }}
where status = 'completed'
