use anyhow::Result;
use axum::http::HeaderMap;
use bytes::Bytes;
use reqwest::StatusCode;
use std::time::Duration;

pub struct Upstream {
    client: reqwest::Client,
    target: String,
}

impl Upstream {
    pub fn new(target: String) -> Self {
        let client = reqwest::Client::builder()
            .timeout(Duration::from_secs(120))
            .build()
            .expect("failed to build HTTP client");
        Self { client, target }
    }

    pub async fn post(&self, path: &str, headers: &HeaderMap, body: Bytes) -> Result<(StatusCode, Bytes)> {
        let url = format!("{}{}", self.target, path);
        let mut req = self.client.post(&url).body(body);

        for (name, value) in headers {
            let name_str = name.as_str();
            if name_str == "content-type" || name_str == "authorization" {
                req = req.header(name, value);
            }
        }

        let resp = req.send().await?;
        let status = resp.status();
        let bytes = resp.bytes().await?;
        Ok((status, bytes))
    }

    pub async fn get(&self, path: &str) -> Result<(StatusCode, Bytes)> {
        let url = format!("{}{}", self.target, path);
        let resp = self.client.get(&url).send().await?;
        let status = resp.status();
        let bytes = resp.bytes().await?;
        Ok((status, bytes))
    }
}
