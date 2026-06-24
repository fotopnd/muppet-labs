// API response shapes — snake_case to match Pydantic output

export type GameStatus = 'scheduled' | 'live' | 'complete'

export type PlayerDetail = {
  player_id: number
  first_name: string
  last_name: string
  position: string
  year: number
  jersey_num: number
  height_ft: number
  height_in: number
  weight_lbs: number
  hometown: string
  state: string
  program_id: number
  program_name: string
  program_emoji: string
  conglomerate_code: string
  pass_attempts: number
  pass_completions: number
  pass_yards: number
  pass_tds: number
  interceptions: number
  rush_attempts: number
  rush_yards: number
  rush_tds: number
  targets: number
  receptions: number
  receiving_yards: number
  receiving_tds: number
  tackles: number
  sacks: number
  ints_def: number
  forced_fumbles: number
  fg_attempts: number
  fg_made: number
  games_played: number
}

export type CoachSeasonRow = {
  season: number
  program_name: string
  program_emoji: string
  wins: number
  losses: number
  win_pct: number
  off_yards: number
  pass_yards: number
  rush_yards: number
  def_yards_allowed: number
  sacks: number
  interceptions: number
  games_played: number
}

export type CoachDetail = {
  coach_id: number
  first_name: string
  last_name: string
  role: string
  rating: number
  program_id: number
  program_name: string
  program_emoji: string
  conglomerate_code: string
  seasons: CoachSeasonRow[]
}

export type ConglomerateOut = {
  id: number
  code: string
  full_name: string
  network: string
  region: string
  primary_color: string
  secondary_color: string
}

export type ProgramStanding = {
  id: number
  name: string
  emoji: string
  city: string
  tier: number
  elo: number
  wins: number
  losses: number
}

export type ConglomerateStandings = {
  conglomerate: ConglomerateOut
  tier1: ProgramStanding[]
  tier2: ProgramStanding[]
}

export type ProgramSummary = {
  id: number
  name: string
  emoji: string
  city: string
  tier: number
  elo: number
  conglomerate_code: string
  wins: number
  losses: number
}

export type ProgramDetail = {
  id: number
  name: string
  emoji: string
  city: string
  mascot: string
  tier: number
  elo: number
  primary_color: string
  secondary_color: string
  conglomerate_id: number
  conglomerate_code: string
  wins: number
  losses: number
}

export type ProgramScheduleGame = {
  game_id: number
  week: number
  broadcast_slot: string
  status: GameStatus
  home_score: number
  away_score: number
  is_home: boolean
  opponent_name: string
  opponent_emoji: string
}

export type PlayerRoster = {
  player_id: number
  first_name: string
  last_name: string
  position: string
  year: number
  jersey_num: number
}

export type StatLeader = {
  player_id: number
  name: string
  total_yards: number
  tds: number
  games_played: number
}

export type ProgramStats = {
  passers: StatLeader[]
  rushers: StatLeader[]
  receivers: StatLeader[]
}

export type ScheduleGame = {
  game_id: number
  week: number
  broadcast_slot: string
  status: GameStatus
  home_score: number
  away_score: number
  home_program_id: number
  home_name: string
  home_emoji: string
  away_program_id: number
  away_name: string
  away_emoji: string
}

export type WeekSchedule = {
  week: number
  games: ScheduleGame[]
}

export type ProgramRef = {
  program_id: number
  name: string
  emoji: string
  city: string
  elo_pre: number
  elo_post: number | null
}

export type GameDetail = {
  id: number
  week: number
  broadcast_slot: string
  status: GameStatus
  is_rivalry: boolean
  is_postseason: boolean
  elo_tiebreak: boolean
  home_score: number
  away_score: number
  home: ProgramRef
  away: ProgramRef
}

export type PlayerBoxscore = {
  player_id: number
  name: string
  position: string
  pass_yards: number
  pass_tds: number
  pass_attempts: number
  pass_completions: number
  rush_yards: number
  rush_tds: number
  rush_attempts: number
  receiving_yards: number
  receiving_tds: number
  receptions: number
  targets: number
  sacks: number
  ints_def: number
}

export type GameBoxscore = {
  home: PlayerBoxscore[]
  away: PlayerBoxscore[]
}

export type GamePlay = {
  play_number: number
  quarter: number
  possession: string
  play_type: string
  yards_gained: number | null
  field_pos_before: number
  field_pos_after: number | null
  score_home: number
  score_away: number
  description: string
  down?: number | null
  distance?: number | null
}

export type LeaderboardEntry = {
  player_id: number
  name: string
  program_name: string
  total_yards: number
  tds: number
  games_played: number
}

export type Leaderboards = {
  passers: LeaderboardEntry[]
  rushers: LeaderboardEntry[]
  receivers: LeaderboardEntry[]
}

// SSE event shapes — from orchestrator.py stream_game_replay

export type SsePlayEvent = {
  game_id: number
  play_number: number
  quarter: number
  possession: string
  play_type: string
  yards_gained: number | null
  field_pos_before: number
  field_pos_after: number | null
  score_home: number
  score_away: number
  primary_player_id: number | null
  description: string
  x: number | null
  y: number | null
  down: number | null
  distance: number | null
}

// Live scoreboard and leaders
export type LiveScore = {
  game_id: number
  score_home: number
  score_away: number
  quarter: number
  possession: string
}

export type LiveLeader = {
  player_id: number
  name: string
  program_name: string
  program_emoji: string
  game_id: number
  yards: number
}

export type LiveLeaders = {
  passers: LiveLeader[]
  rushers: LiveLeader[]
  receivers: LiveLeader[]
}

export type ProgramEloRank = {
  id: number
  name: string
  emoji: string
  conglomerate_id: number
  tier: number
  elo: number
  pre_season_elo: number
  season_delta: number
}

export type NafcaLeaderboard = {
  lifetime: ProgramEloRank[]
  season: ProgramEloRank[]
}

// Gamecast internal state
export type GamecastState =
  | { status: 'loading' }
  | { status: 'scheduled'; game: GameDetail }
  | {
      status: 'live'
      game: GameDetail
      plays: GamePlay[]
      home_score: number
      away_score: number
      quarter: number
      down: number | null
      distance: number | null
      field_pos: number | null
      possession: string | null
      boxscore: GameBoxscore
    }
  | { status: 'complete'; game: GameDetail; plays: GamePlay[]; boxscore: GameBoxscore }
