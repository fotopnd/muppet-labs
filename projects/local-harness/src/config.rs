use serde::{Deserialize, Serialize};
use std::path::PathBuf;

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Config {
    #[serde(default = "default_port")]
    pub port: u16,
    #[serde(default = "default_target")]
    pub target: String,
    #[serde(default = "default_log_path")]
    pub log_path: PathBuf,
}

fn default_port() -> u16 {
    8080
}

fn default_target() -> String {
    "http://localhost:11434".to_string()
}

fn default_log_path() -> PathBuf {
    let home = std::env::var("HOME").unwrap_or_else(|_| ".".to_string());
    PathBuf::from(home).join(".local/share/lh/requests.jsonl")
}

impl Default for Config {
    fn default() -> Self {
        Self {
            port: default_port(),
            target: default_target(),
            log_path: default_log_path(),
        }
    }
}

impl Config {
    pub fn load() -> Self {
        std::fs::read_to_string("harness.toml")
            .ok()
            .and_then(|s| toml::from_str(&s).ok())
            .unwrap_or_default()
    }
}
