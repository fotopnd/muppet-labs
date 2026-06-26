# Brief: graduation-portal

**Role:** brief
**Sprint unit:** 04
**Project:** gridiron
**Date:** 2026-06-26
**Status:** COMPLETE

## Summary

Migration `a1b2c3d4e5f7` makes `players.program_id` nullable. `run_graduation` and `run_portal` added to `gridiron/engine/offseason.py`.

**Graduation:** all yr5 depart; 70% yr4 graduate; 12% of high-attribute (avg≥0.55) yr3 leave early. Departed players get `program_id=NULL`. Remaining players get `class_year += 1`.

**Portal:** reasons = `record` (winpct<0.25, 15% chance), `playing_time` (high attr at low-ELO program, 10% chance), `random` (2.5%). Resolution: each program bids `score = 0.40×norm_elo + 0.20×tier_bonus + 0.25×pos_need + 0.15×noise`; current school gets +0.15 retention bonus. Transfer cap = 5 incoming per program. Jersey conflict on transfer → pick new available jersey.
