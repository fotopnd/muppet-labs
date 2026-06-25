use std::sync::Arc;
use std::time::Instant;

use axum::{
    body::Bytes,
    extract::State,
    http::{HeaderMap, HeaderValue, StatusCode},
    response::{IntoResponse, Response},
    routing::{get, post},
    Router,
};
use chrono::Utc;

use crate::{
    cli::UpArgs,
    config::Config,
    logger::{LogEntry, Logger},
    upstream::Upstream,
};

/// When the request included tools, a real success requires tool_calls to be
/// a non-empty array in choices[0].message. A valid JSON response that puts
/// the call in `content` instead counts as a failure.
fn check_parse_ok(raw: &str, had_tools: bool) -> bool {
    let Ok(v) = serde_json::from_str::<serde_json::Value>(raw) else {
        return false;
    };
    if !had_tools {
        return true;
    }
    v["choices"][0]["message"]["tool_calls"]
        .as_array()
        .map(|a| !a.is_empty())
        .unwrap_or(false)
}

#[derive(Clone)]
struct AppState {
    upstream: Arc<Upstream>,
    logger: Arc<Logger>,
}

pub async fn run(args: UpArgs) -> anyhow::Result<()> {
    let mut config = Config::load();

    config.port = args.port;
    config.target = args.target;
    if let Some(log) = args.log {
        config.log_path = log;
    }

    let logger = Logger::new(config.log_path.clone()).await?;

    println!("lh up");
    println!("  listening  →  http://0.0.0.0:{}", config.port);
    println!("  upstream   →  {}", config.target);
    println!("  log        →  {}", config.log_path.display());

    let state = AppState {
        upstream: Arc::new(Upstream::new(config.target)),
        logger: Arc::new(logger),
    };

    let app = Router::new()
        .route("/v1/chat/completions", post(handle_completions))
        .route("/v1/models", get(handle_models))
        .with_state(state);

    let addr = format!("0.0.0.0:{}", config.port);
    let listener = tokio::net::TcpListener::bind(&addr).await?;
    axum::serve(listener, app).await?;
    Ok(())
}

async fn handle_completions(
    State(state): State<AppState>,
    headers: HeaderMap,
    body: Bytes,
) -> Response {
    let start = Instant::now();

    let req: serde_json::Value = serde_json::from_slice(&body).unwrap_or_default();
    let model = req["model"].as_str().map(|s| s.to_string());
    let had_tools = req
        .get("tools")
        .and_then(|t| t.as_array())
        .map(|a| !a.is_empty())
        .unwrap_or(false);
    let is_stream = req["stream"].as_bool().unwrap_or(false);

    match state.upstream.post("/v1/chat/completions", &headers, body).await {
        Ok((status, resp_body)) => {
            let latency_ms = start.elapsed().as_millis() as u64;

            let (raw_response, parse_ok) = if is_stream {
                // Phase 0a: streaming responses are forwarded but not captured
                (None, None)
            } else {
                let raw = String::from_utf8_lossy(&resp_body).to_string();
                let ok = check_parse_ok(&raw, had_tools);
                (Some(raw), Some(ok))
            };

            let entry = LogEntry {
                ts: Utc::now(),
                model,
                had_tools,
                stream: is_stream,
                raw_response,
                parse_ok,
                latency_ms,
            };

            let logger = Arc::clone(&state.logger);
            tokio::spawn(async move { logger.write(entry).await });

            let mut response = (status, resp_body).into_response();
            response
                .headers_mut()
                .insert("content-type", HeaderValue::from_static("application/json"));
            response
        }
        Err(e) => (
            StatusCode::BAD_GATEWAY,
            format!("upstream error: {e}\n\nIs Ollama running? Try: ollama serve"),
        )
            .into_response(),
    }
}

async fn handle_models(State(state): State<AppState>) -> Response {
    match state.upstream.get("/v1/models").await {
        Ok((status, body)) => {
            let mut response = (status, body).into_response();
            response
                .headers_mut()
                .insert("content-type", HeaderValue::from_static("application/json"));
            response
        }
        Err(e) => (
            StatusCode::BAD_GATEWAY,
            format!("upstream error: {e}"),
        )
            .into_response(),
    }
}
