# Brief: offseason-api-full

**Role:** brief
**Sprint unit:** 07
**Project:** gridiron
**Date:** 2026-06-26
**Status:** COMPLETE

## Summary

Replaced 501 stubs in `gridiron/api/routers/offseason.py` with real endpoints:
- `POST /offseason/run-graduation` → calls `run_graduation(run_id, season_number, conn)`
- `POST /offseason/run-portal` → calls `run_portal(...)`
- `POST /offseason/run-recruiting` → calls `run_recruiting(...)`
- `POST /offseason/run-training-camp` → calls `run_training_camp(...)`

All take `{"season_number": int, "sim_run_id": int|null}` body. All lazy-import the gitignored engine module. All use `engine.begin()` for the bulk write transaction.
