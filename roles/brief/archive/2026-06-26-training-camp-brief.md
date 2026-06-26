# Brief: training-camp

**Role:** brief
**Sprint unit:** 06
**Project:** gridiron
**Date:** 2026-06-26
**Status:** COMPLETE

## Summary

`run_training_camp` added to `gridiron/engine/offseason.py`.

**Attribute gain by class_year:** yr1=+0.040, yr2=+0.028, yr3=+0.016, yr4=+0.008, yr5=+0.004 (all Gaussian μ=gain, σ=0.4×gain). Capped at 1.0.

**Injury clear:** all active players set to `injury_status='healthy'`.

**ELO regression:** `UPDATE programs SET elo = 1500 + (elo - 1500) * 0.85` — 15% regression toward 1500 per off-season.
