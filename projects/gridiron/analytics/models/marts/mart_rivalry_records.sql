with outcomes as (select * from {{ ref('int_game_outcomes') }}),
     pairs    as (select * from {{ source('gridiron', 'rivalry_pairs') }})

select
    least(o.home_program_id, o.away_program_id)                 as program_a_id,
    greatest(o.home_program_id, o.away_program_id)              as program_b_id,
    case
        when o.home_program_id < o.away_program_id then o.home_program_name
        else o.away_program_name
    end                                                         as program_a_name,
    case
        when o.home_program_id < o.away_program_id then o.away_program_name
        else o.home_program_name
    end                                                         as program_b_name,
    count(*)                                                    as games_played,
    sum(case when winner_program_id = least(o.home_program_id, o.away_program_id)
        then 1 else 0 end)                                      as program_a_wins,
    sum(case when winner_program_id = greatest(o.home_program_id, o.away_program_id)
        then 1 else 0 end)                                      as program_b_wins,
    round(avg(abs(o.margin)), 1)                                as avg_margin,
    max(o.ended_at)                                             as last_played
from outcomes o
join pairs p
  on least(o.home_program_id, o.away_program_id)    = p.program_a_id
 and greatest(o.home_program_id, o.away_program_id) = p.program_b_id
group by 1, 2, 3, 4
