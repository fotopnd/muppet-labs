use anyhow::Result;
use chrono::{DateTime, Utc};
use serde::{Deserialize, Serialize};
use std::path::PathBuf;
use std::sync::Arc;
use tokio::fs::{self, OpenOptions};
use tokio::io::AsyncWriteExt;
use tokio::sync::Mutex;

#[derive(Debug, Serialize, Deserialize)]
pub struct LogEntry {
    pub ts: DateTime<Utc>,
    pub model: Option<String>,
    pub had_tools: bool,
    pub stream: bool,
    pub raw_response: Option<String>,
    pub parse_ok: Option<bool>,
    pub latency_ms: u64,
}

#[derive(Clone)]
pub struct Logger {
    pub path: PathBuf,
    file: Arc<Mutex<fs::File>>,
}

impl Logger {
    pub async fn new(path: PathBuf) -> Result<Self> {
        if let Some(parent) = path.parent() {
            fs::create_dir_all(parent).await?;
        }
        let file = OpenOptions::new()
            .create(true)
            .append(true)
            .open(&path)
            .await?;
        Ok(Self {
            path,
            file: Arc::new(Mutex::new(file)),
        })
    }

    pub async fn write(&self, entry: LogEntry) {
        let Ok(mut line) = serde_json::to_string(&entry) else {
            return;
        };
        line.push('\n');
        let mut f = self.file.lock().await;
        let _ = f.write_all(line.as_bytes()).await;
    }
}

pub async fn tail(args: crate::cli::LogsArgs) -> Result<()> {
    let config = crate::config::Config::load();
    let path = args.log.unwrap_or(config.log_path);

    let contents = fs::read_to_string(&path).await.unwrap_or_default();

    let entries: Vec<LogEntry> = contents
        .lines()
        .filter_map(|line| serde_json::from_str(line).ok())
        .collect();

    let filtered: Vec<&LogEntry> = if args.failures_only {
        entries
            .iter()
            .filter(|e| e.parse_ok == Some(false))
            .collect()
    } else {
        entries.iter().collect()
    };

    let start = filtered.len().saturating_sub(args.tail);
    for entry in &filtered[start..] {
        let ts = entry.ts.format("%H:%M:%S").to_string();
        let model = entry.model.as_deref().unwrap_or("unknown");
        let status = match entry.parse_ok {
            Some(true) => "ok ",
            Some(false) => "ERR",
            None => "~  ",
        };
        let tools = if entry.had_tools { "tools" } else { "     " };
        println!(
            "[{}] {} {} {:>4}ms  {}  {}",
            ts,
            status,
            tools,
            entry.latency_ms,
            model,
            entry
                .raw_response
                .as_deref()
                .unwrap_or("")
                .chars()
                .take(80)
                .collect::<String>()
                .replace('\n', " ")
        );
    }

    if filtered.is_empty() {
        println!("no entries{}", if args.failures_only { " (failures only)" } else { "" });
    }

    Ok(())
}
