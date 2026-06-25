use clap::Parser;
use cli::{Cli, Commands};

mod cli;
mod config;
mod logger;
mod proxy;
mod upstream;

#[tokio::main]
async fn main() -> anyhow::Result<()> {
    let cli = Cli::parse();
    match cli.command {
        Commands::Up(args) => proxy::run(args).await,
        Commands::Logs(args) => logger::tail(args).await,
    }
}
