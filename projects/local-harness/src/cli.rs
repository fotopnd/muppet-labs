use clap::{Args, Parser, Subcommand};
use std::path::PathBuf;

#[derive(Parser)]
#[command(name = "lh", about = "Local LLM harness — logging proxy for tool-call research")]
pub struct Cli {
    #[command(subcommand)]
    pub command: Commands,
}

#[derive(Subcommand)]
pub enum Commands {
    /// Start the proxy daemon
    Up(UpArgs),
    /// Read captured request logs
    Logs(LogsArgs),
}

#[derive(Args)]
pub struct UpArgs {
    /// Port to listen on
    #[arg(short, long, default_value = "8080", env = "LH_PORT")]
    pub port: u16,

    /// Upstream Ollama URL
    #[arg(short, long, default_value = "http://localhost:11434", env = "LH_TARGET")]
    pub target: String,

    /// Path to write JSONL log (overrides harness.toml)
    #[arg(short, long, env = "LH_LOG")]
    pub log: Option<PathBuf>,
}

#[derive(Args)]
pub struct LogsArgs {
    /// Number of entries to show
    #[arg(short, long, default_value = "20")]
    pub tail: usize,

    /// Show only entries where parse_ok is false
    #[arg(long)]
    pub failures_only: bool,

    /// Log file path (defaults to harness.toml / system default)
    #[arg(short, long, env = "LH_LOG")]
    pub log: Option<PathBuf>,
}
