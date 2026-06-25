select
    id          as coach_id,
    program_id,
    role,
    first_name,
    last_name,
    first_name || ' ' || last_name as full_name,
    rating,
    created_at
from {{ source('gridiron', 'coaches') }}
