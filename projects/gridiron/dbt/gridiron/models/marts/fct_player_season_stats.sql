-- Aggregate player_game_stats to season level via game.season
select
    g.season,
    s.player_id,
    s.program_id,
    p.full_name         as player_name,
    p.position,
    p.position_group,
    p.class,
    pr.program_name,
    pr.conglomerate_code,
    count(distinct s.game_id)           as games_played,
    -- passing
    sum(s.pass_attempts)                as pass_attempts,
    sum(s.pass_completions)             as pass_completions,
    sum(s.pass_yards)                   as pass_yards,
    sum(s.pass_tds)                     as pass_tds,
    sum(s.interceptions)                as interceptions,
    case when sum(s.pass_attempts) > 0
        then round((sum(s.pass_completions)::numeric / sum(s.pass_attempts)) * 100, 1)
    end                                 as completion_pct,
    -- rushing
    sum(s.rush_attempts)                as rush_attempts,
    sum(s.rush_yards)                   as rush_yards,
    sum(s.rush_tds)                     as rush_tds,
    case when sum(s.rush_attempts) > 0
        then round(sum(s.rush_yards)::numeric / sum(s.rush_attempts), 1)
    end                                 as yards_per_carry,
    -- receiving
    sum(s.targets)                      as targets,
    sum(s.receptions)                   as receptions,
    sum(s.receiving_yards)              as receiving_yards,
    sum(s.receiving_tds)                as receiving_tds,
    -- defense
    sum(s.tackles)                      as tackles,
    sum(s.sacks)                        as sacks,
    sum(s.forced_fumbles)               as forced_fumbles,
    sum(s.ints_def)                     as defensive_ints,
    -- special teams
    sum(s.fg_attempts)                  as fg_attempts,
    sum(s.fg_made)                      as fg_made,
    -- total touchdowns (all phases)
    sum(s.pass_tds + s.rush_tds + s.receiving_tds) as total_tds
from {{ ref('stg_player_game_stats') }} s
inner join {{ ref('stg_games') }} g using (game_id)
left join {{ ref('dim_players') }} p using (player_id)
left join {{ ref('dim_programs') }} pr on pr.program_id = s.program_id
where g.status = 'complete'
group by
    g.season, s.player_id, s.program_id,
    p.full_name, p.position, p.position_group, p.class,
    pr.program_name, pr.conglomerate_code
