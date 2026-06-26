# Brief: recruiting

**Role:** brief
**Sprint unit:** 05
**Project:** gridiron
**Date:** 2026-06-26
**Status:** COMPLETE

## Summary

`run_recruiting` added to `gridiron/engine/offseason.py`.

**Scoring:** `0.35×norm_elo + 0.15×tier_bonus + 0.25×prestige_match + 0.15×pos_need + 0.10×noise`. Tier 1 gets +0.10, tier 3+ gets -0.05.

**Slots:** 85 total roster cap, 25/year cap minus transfers_in already resolved. Programs with full slots skip prospects.

**Player creation:** uses prospect's first_name/last_name, position expanded (OL→LT/LG/C/RG/RT etc.), `class_year=1`, attrs from `_attrs_from_rating(rating)` = base 0.25 + rating×0.30 ± σ=0.04. Jersey assigned collision-free.

**Prospect status:** updated to `signed` (committed_program_id set) or `no_offer`.
