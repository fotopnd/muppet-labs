# Gridiron — Design Document

> This document is the primary input for the planner and architect roles.
> Fill in each section before running the planner.
> Leave a section blank if undecided — the planner will flag it as an open question.

---

## 1. Concept

_One paragraph. What is this, what does it feel like to watch it, what makes it interesting?_

We are running a live idle simulation of a future college football world where all conferences have been 
taken over by corporate broadcasting or similar conglomerates.  They have taken full control and the game is a capitalist grimdark adventure
Teams play 26 weeks of the year like a full Formula 1 schedule.  There are all sorts of bells and whistles to the game but now one thing is clear
More Football More Of The Time

---

## 2. The Universe

### 2.1 Teams

_How many teams? Are they organised into conferences? Do they have personalities, home cities, mascots?_

There are 130 teams organized into 5 conferences of 26 teams.  each conference has tier 1 and tier 2 with promotion and relegation.
we will take the existing college football landscape and re-map school and team names to be legally distinct
stadiums will be relocated and renamed from current real world to nearby cities and towns. 

### 2.2 Players

_Named players or anonymous positions? How many per roster? Do player stats persist across seasons?_

We will need to be generating names for players, coaches, and boosters.  
We will need to build a distinct engine that is capable of generating these at least once a season as players graduate etc
We will also need to be generating player base statistics like height, weight, game attributes like speed strength, technical attributes like passing and catching, and secret attributes to be determined 

### 2.3 World flavour

_Blaseball had absurdist lore — peanuts, incineration, forbidden knowledge. Does gridiron have a flavour layer, or is it straight simulation?_

This is the hyper capitalist version of the current corporate conglomeration of college sports.  private equity, NIL, mega broadcast deals.
Amateurism is not dead, but it is now completely owned through a collection of monied interests, including broadcast networks, commercial branding opportunities, and alumni boosterism.  And we love it.  We can't get enough of it.  More Football More of the Time.
The game will be a straight simulation.  The gameplay and statistics will be realistic.  There will be some flourishes to attribute bonuses and de-buffs, but mostly a recognizable version of current football.  We are not reinventing the wheel or creating a wild fantasy version of the game.
However, the corporate wars subtext is heavily influenced by Rollerball of the 1970s starring James Caan.

---

# 3. Season Structure

### 3.1 Regular Season

*   **Total Duration:** 26 Weeks.
*   **Games Per Week:** 60 games per week across the entire 130-team engine (12 games per 26-team broadcast conglomerate; 6 games per 13-team tier).
*   **Weekly Team Participation:** Due to the odd number of teams per tier (13), exactly **one team per tier will be on a bye week each round**. Over a 26-week cycle, every program plays 24 regular season games and receives 2 bye weeks.
*   **The Rivalry Window:** Weeks 25 and 26 are reserved for the cross-tier "Exhibition Shield" window. The standard round-robin scheduling pauses, and the engine maps historic regional or cross-network rivalries (e.g., matching a Tier 1 team against a Tier 2 team from a different network, like an out-of-conference Florida vs. Florida State) to protect legacy matchups while keeping the closed table math pristine.

### 3.2 Postseason

*   **V1 Status:** **Confirmed (Full 32-Team Postseason Tournament with Tier 2 Pathways).**
*   **Scope Definition:** A comprehensive, high-stakes tournament is fully in scope for V1 to deliver the definitive payoff of the corporate super-league model. The format mimics a massive, world-class bracket tournament, establishing an explicit, highly marketable path for Tier 2 organizations to claim both regional prestige and a national championship shot.
*   **Conference Championship Structure:**
    *   To preserve historic rivalries and television billing, each of the 5 Broadcast Conglomerates hosts an end-of-season Conference Championship Game.
    *   The matchup pits the **Tier 1 Regular Season Champion** directly against the **Tier 2 Regular Season Champion**. 
    *   This dynamic gives Tier 2 champions an immediate, high-profile opportunity to win their explicit Conference Championship outright on national television prior to the national bracket selection.
*   **Qualification & Seeding Logic:**
    *   **Automatic Bids (10 Teams):** The winners and runners-up of the 5 Conference Championship Games secure automatic qualification into the 32-team national tournament. If a Tier 2 champion wins the game, they secure the conference's #1 automatic bid; if they lose, they remain highly viable for an At-Large selection based on their resume.
    *   **At-Large Bids (22 Teams):** The remaining 22 slots are filled dynamically by the simulation engine's automated Elo rating script, evaluating all remaining teams across both tiers.
    *   **Tier 2 Guaranteed Bracket Pathway:** To ensure a Cinderella path is hardcoded into the system, the top 2 highest-ranked Tier 2 champions by final Elo rating are guaranteed automatic At-Large bids into the 32-team bracket, irrespective of their Conference Championship Game outcome.
*   **Bracket Execution:** 
    *   The tournament runs as a single-elimination, 5-round bracket spanning 5 postseason weeks.
    *   Teams are seeded 1 through 32 based on their final Elo rating, with initial rounds structured to prioritize cross-network matchups to maximize broadcast ratings.
    *   Tier 2 promotion remains tied to regular-season table finish, allowing an ascending team to simultaneously chase a deep postseason run while securing their Tier 1 placement for the following year.
    *   **The Ultimate Ascent Clause (Championship Promotion):** In the event that a Tier 2 program enters the 32-team national tournament via an At-Large bid and wins the National Championship, that program automatically bypasses all standard table-based restrictions and triggers immediate promotion to Tier 1 for the upcoming season. If the program had already secured promotion via a top-two regular-season table finish, this clause instead protects the next highest-ranking Tier 2 team on that network's leaderboard, creating a third promotion slot for that conglomerate to reward the network's breakout year. Tier 1 would have bottom 3 relegation teams in that case.

### 3.3 Season Reset

*   **Hard Resets (Wiped Data):**
    *   Team win-loss records, conference standings tables, and current-season box scores are completely cleared to reset the data layer for the next annual cycle.
*   **Soft Resets (Data Carried Over):**
    *   **Player Database:** The four-year graduation clock advances. Seniors and draft-eligible juniors are purged from the database. Remaining players advance one year in eligibility, trigger their progression/regression attribute updates, and vacant roster spots are filled via the recruiting and transfer portal loop.
    *   **Historical Archive:** Cumulative player career statistics, historic team win-loss tracking, and the chronological list of legacy National and Tier Champions are written to a permanent historical archive table to build continuous simulation lore.
*   **The Corporate Shift (Promotion/Relegation):** Before the schedule generator triggers for the new season, the database executes the boardroom swap. The bottom 2 teams from each Tier 1 leaderboard swap their tier identifiers with the top 2 teams from their respective Tier 2 leaderboard. Media rights revenue flags are updated accordingly, instantly modifying team budgets for the upcoming roster-building cycle.

---

## 4. Simulation

### 4.1 Game Cadence

*   **Real-Time Execution:** A full 60-minute football game simulates in approximately **5 to 10 seconds** of compute time on the backend server.
*   **Time-Dilated Streaming Window:** For the user-facing interface, the engine streams play-by-play events down to the client via a time-dilated socket connection over **10 real-time minutes** per game. 
*   **Engine Throughput:** The engine is built to process a full weekly slate (60 games) simultaneously in memory within **30 seconds**, broadcasting synchronous live tick-updates to the frontend display.

### 4.2 Play Granularity

*   **Definition of a "Play":** A single atomic state transition in the game loop that consumes time from the game clock, modifies field position, updates downs/distance, and adjusts player/team state variables. A typical game generates between 120 and 150 total plays.
*   **Core Event Types:**
    *   `KICKOFF` / `PUNT` / `FIELD_GOAL_ATTEMPT` (Special Teams actions with varying block, return, and success rates).
    *   `RUSH` (Hand-off mechanics tracking yards gained, tackles broken, or yards lost).
    *   `PASS_COMPLETE` / `PASS_INCOMPLETE` / `PASS_DEFLECTION` (Aerial metrics driving spatial progress and receiver/defensive back matchups).
    *   `TOUCHDOWN` / `SAFETY` / `PAT_CONVERSION` / `TWO_POINT_CONVERSION` (Scoring logic triggers).
    *   `TURNOVER_INTERCEPTION` / `TURNOVER_FUMBLE` (Possession flip mechanisms).
    *   `SACK` / `TACKLE_FOR_LOSS` / `PENALTY` (Negative progression blocks).

### 4.3 Randomness and Balance

*   **Simulation Balance Philosophy:** The engine favors **grounded realism grounded in Elo and attribute disparities**, ensuring that blue-blood programs consistently dominate lower-rated rosters over a 24-game sample size.
*   **The "Primetime Drama" Multiplier:** To capture the volatile nature of college football and network television narratives, a scaling variance factor is introduced exclusively during **Rivalry Windows (Weeks 25-26)** and the **32-Team Postseason Tournament**. Under this multiplier, the probability of critical variance events (e.g., turnovers, blown coverages, momentum shifts) increases by 15%, giving lower-tier underdogs a mathematically viable "Cinderella" window without corrupting regular-season integrity.

### 4.4 What the Engine Does NOT Simulate

*   **Out of Scope for V1:**
    *   **In-Game Injuries:** Rosters operate at 100% physical availability throughout the season; there is no attribute degradation or player benching due to physical trauma.
    *   **Dynamic Weather:** All games are executed under standardized, neutral climate parameters. Wind speed, rain, and snow mechanics are completely ignored by the physics and probability matrices.
    *   **Real-Time Coaching Decisions:** There are no active micro-management inputs during execution (e.g., calling timeouts, choosing specific formations, challenging referee plays). Teams run entirely on pre-compiled, attribute-driven macro playbooks.
    *   **Off-Field Discipline or Academic Eligibility:** Player status is strictly driven by the graduation clock and transfer portal states; off-field operational noise is excluded from the engine.

---

---

## 5. Data and Events

### 5.1 What Gets Stored

*   **Persistent Database Storage (Write to DB):**
    *   **The Full Play Ledger:** Every single play event generated by the engine (120 to 150 plays per game) is written to a compressed, relational `play_log` table. This is mandatory to fuel the granular, down-by-down statistical aggregation engine for all 22 players on the field.
    *   Final game box scores containing total team metrics, scoring summaries, and stadium metadata.
    *   End-of-week standings, promotion/relegation table status, and updated Elo ratings.
*   **Ephemeral Data (Computed in Memory and Discarded):**
    *   Real-time physics vector data or micro-positional player coordinates used to compute structural play outcomes during the live 5-minute client streaming window. Once the play resolution is determined and mapped to a structured event, the raw physics coordinates are instantly flushed.

### 5.2 Stats Tracked

The database architecture maintains deep tracking arrays across all position groups to ensure every athlete impacts the team's footprint and player progression metrics.

#### Per-Game & Per-Season Team Stats
*   Points scored per quarter, point differential, total first downs, third/fourth-down efficiency, total explosive plays (plays gaining 20+ yards), turnover margin, and total time of possession.

#### Per-Game & Per-Season Individual Player Stats

*   **Quarterbacks:** Pass attempts, completions, passing yards, passing touchdowns, interceptions, times sacked, rushing attempts, rushing yards, rushing touchdowns, and turnover fumbles.
*   **Skill Positions (RB / WR / TE):** Rushing attempts, rushing yards, yards after contact, targets, receptions, receiving yards, yards after catch (YAC), drop count, total touchdowns, and fumbles lost.
*   **Offensive Linemen (LT / LG / C / RG / RT):** 
    *   *Pass Blocking:* Pass-blocking snaps, pressures allowed, hurries allowed, hits allowed, and sacks allowed.
    *   *Run Blocking:* Run-blocking snaps, "pancake" blocks, blown assignments, and run-stuff rate allowed (runs stopped for 0 or fewer yards behind that lineman's structural gap).
*   **Individual Defensive Players (DL / EDGE / LB / CB / S):**
    *   *Pass Rush:* Pass-rush snaps, sacks, quarterback hits, quarterback hurries, and total pressures generated.
    *   *Run Defense:* Solo tackles, assisted tackles, tackles for loss (TFL), defensive stops (tackles resulting in a failure for the offense based on down and distance), and forced fumbles.
    *   *Pass Coverage:* Coverage snaps, targets allowed, receptions allowed, receiving yards allowed, pass deflections, interceptions, and defensive touchdowns.
*   **Special Teams:** Field goal attempts/makes (categorized by distance bands: 20-29, 30-39, 40-49, 50+ yards), punts, net punting average, punts pinned inside the 20-yard line, kickoff/punt return yards, and return touchdowns.

### 5.3 Replay

_What does a game replay contain? Is it the full event log, or a condensed summary?_

*   **Replay Content Architecture:** To deliver a premium, high-fidelity Gamecast experience mimicking a modern sports network application, a game replay does **not** rely on a static, flat text summary. Instead, it contains the **Complete Chronological Event Stream (`event_stream`)** compiled by the engine during simulation. 
*   **The Gamecast Schema:** Every stored play entry in the database houses a highly structured JSON state packet. When a user opens a replay, the client pulls this timeline to completely reconstruct the game's momentum from kickoff to the final whistle. The data payload for the replay engine contains:
    *   **The Play State Wrapper:** Time remaining on the game clock, quarter, current down, distance-to-gain, field position (yard line), and current score.
    *   **The Structural Description String:** A dynamically assembled, variable-mapped text string describing the play execution (e.g., *"Jaxson Dart passes complete to Tre Harris for a 14-yard gain to the UK 45-yard line. Tackled by Maxwell Hairston."*).
    *   **Statistical Delta Packets:** Explicit notation of which player profiles received statistical markers on that down (e.g., mapping `+14 passing_yards` to QB, `+14 receiving_yards` and `+6 YAC` to WR, and `+1 solo_tackle` to CB) to drive real-time updating box score tabs.
    *   **Spatial Vector Coordinate Arrays:** Simplified 2D grid coordinates tracking the path of the ball and the primary attacking/defending players on the field. This allows the frontend UI to render an animated "Drive Tracker" visual showing the ball progressing across a virtual 100-yard field interface.
*   **User Interface Modes:** The replay system exposes three scannable viewing filters for the user:
    1.  **All Plays (Full Timeline):** A comprehensive, scrollable feed of all 120 to 150 plays executed during the match.
    2.  **Key Plays Only:** A filtered view displaying exclusively scoring drives, turnovers, fourth-down conversions, and explosive plays of 20+ yards.
    3.  **Drive Chart Summary:** A macro-level visual breakdown of each possession, logging total plays, net yardage, time consumed, and the drive outcome (e.g., Touchdown, Punt, Turnover on Downs).
---

## 6. Frontend

### 6.1 Pages

*   **Dashboard / Hub:** The central corporate control center. Displays the global 130-team map, active live ticker alerts for close matches, national headlines driven by Elo shifts, and the current week's broadcasting schedule split by media conglomerate.
*   **Conglomerate Hubs (x5):** Dedicated pages for each of the media ecosystems (e.g., FOX Sports Syndicate, NBC/Peacock Coalition). Features a prominent split showing the Tier 1 and Tier 2 standings tables, the conference championship game predictor, and network revenue metrics.
*   **Team Profile View:** The deep-dive team matrix. Displays current roster attributes, team Elo charts over time, historical trophy cases, budget/media payout indicators, and an interactive team-specific season schedule.
*   **Gamecast Central (Live / Replay):** The immersive game center. Houses the live-streaming play feed, interactive drive charts, real-time animated field trackers, and a fully sorting box score tab.

### 6.2 Live Feed

*   **Visual Interface:** Modeled directly after elite mobile sports applications. The screen features a persistent header tracking the game state (Quarter, Clock, Down/Distance, Timeouts, Possessing Team Indicator, and Score). Below the header, a virtual horizontal 100-yard field interface renders a moving football icon tracking real-time line of scrimmage shifts and passing vectors.
*   **Update Mechanism:** Powered by an active WebSocket connection streaming single-play JSON packets down from the backend memory array every 2 to 3 seconds. The incoming event fires a micro-animation on the field display and stacks a new text play card onto the top of the chronological feed.
*   **At-a-Glance Indicators:** 
    *   **Possession Anchor:** A clear broadcast-style logo or colored dot affixed to the side of the team currently attacking.
    *   **Explosive/Impact Play Tags:** Flashing color-coded borders wrapped around critical event cards (e.g., Crimson for a Turnover, Gold for a Touchdown, Blue for a 20+ yard play) to grab visual attention during fast-paced streaming sessions.

### 6.3 Standings

*   **The Conglomerate Grid:** Displays the 26-team ecosystem divided into two clear 13-team vertical brackets (Tier 1 and Tier 2) on a single screen to highlight the promotion/relegation cutoff boundary.
*   **Filtering Mechanics:** Users can filter globally across all 130 teams or isolate metrics by Conglomerate, Tier, or specific stat leadership groups.
*   **Sorting Hierarchies:**
    *   *Primary Standings:* Sorted explicitly by Conference Win Percentage, Overall Record, Point Differential, and then Automated Elo.
    *   *The Danger Zones:* The bottom two slots of Tier 1 and top two slots of Tier 2 are framed in distinct red and green drop-shadow styles to explicitly indicate the current promotional and relegation paths.
    *   *Player Leaderboards:* Real-time sorting engine for tracking individual statistical leaders across every metric monitored by Section 5.2 (e.g., sorting offensive linemen by lowest sacks allowed or cornerbacks by targets-to-deflection ratios).

### 6.4 Replay Viewer

*   **Timeline Scrubbing:** Features a horizontal match progress bar divided into four quarters. Hovering or scrubbing across the timeline exposes micro-tooltips showing score progression and possession flips, allowing users to instantly jump the play-by-play interface to precise moments of game interest.
*   **Chronological Play List:** A scannable vertical stack displaying all 120+ plays executed during the match. It features toggle buttons to filter down to "All Plays," "Scoring Plays Only," or "Turnovers/Key Downs." Clicking any individual play card instantly populates the box score tabs with that specific point-in-time statistics.
*   **Score Tracker Sync:** The macro score and team dashboard stay tightly bound to the timeline position, updating dynamically as the user scrubs backward or forward through the event database.

### 6.5 Visual Direction

*   **Aesthetic Tone:** Dark mode default, crisp, analytical, and highly corporate. It should feel less like a whimsical video game menu and more like a high-end financial dashboard merged with a premium broadcast data screen.
*   **Color Palette Principles:** Neutral charcoals and matte black background layers to make team colors pop violently. Network hubs adapt their subtle interface styling to match real-world broadcast overlays (e.g., FOX Hub utilizes clean blues and high-contrast whites; CBS relies on sharp golds and geometric lines).
*   **Typography & Density:** Highly scannable monospaced fonts for numerical data tables to ensure columns align beautifully during rapid sorting. High data-density layout choices are prioritized over empty space, capturing the comprehensive feel of an enterprise analytics console.

---

## 7. Portfolio Framing

*   **The Core Narrative:** This project highlights advanced software engineering capability in architecting complex, high-throughput simulation engines with complex data persistence demands. It demonstrates how to translate intricate corporate governance and sports scheduling rule matrices into clean, deterministic backend logic.
*   **Engineering Highlights for Recruiters:**
    *   **Data Pipeline Scalability:** Processing and writing thousands of individual, multi-player nested atomic records simultaneously every week without dropping data layer integrity or creating memory leaks.
    *   **Systemic Optimization:** Managing high-concurrency event broadcasting via WebSockets to feed active client sessions with low-latency streaming simulation data.
    *   **Complex Architectural Design:** Implementing a zero-bug execution of promotion/relegation algorithms that dynamically restructures relational data paths across season boundaries without destroying historical statistics.

---

## 8. Open Questions & Deterministic Rules

*   **Tie-Breaking Engine Constraints:** If two teams finish the regular season with identical conference records, the database resolves standings using an ironclad, programmatic hierarchy: **1. Head-to-Head Record**, followed immediately by **2. National Elo Rating**. If a tie remains past Elo (statistically negligible), point differential acts as the absolute hard fallback to settle the final promotion/relegation slotting.
*   **Scheduling Alignment across Tiers:** The Weeks 25-26 "Exhibition Shield" window features cross-tier matchups that **always affect Elo**. In this model, everything affects Elo—there are no isolated exhibition buffers. These rivalry games carry full statistical weight, influencing national seeding, bracket eligibility, and corporate momentum calculations.
*   **Roster Generation Caps:** To enforce memory layout predictability and block unbounded database bloat over multiple simulation cycles, **every roster is strictly capped at 105 players**. This uniform constraint applies to all 130 teams across the infrastructure, establishing a firm boundary for the recruiting, transfer portal, and player purge execution passes.