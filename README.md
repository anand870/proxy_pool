# ProxyPool - Production-Ready Crawler Proxy IP Pool

[![Tests](https://github.com/anand870/proxy_pool/actions/workflows/test.yml/badge.svg)](https://github.com/anand870/proxy_pool/actions/workflows/test.yml)
[![Python Version](https://img.shields.io/badge/Python-3.8--3.12-blue.svg)](https://docs.python.org/3/)
[![License](https://img.shields.io/packagist/l/doctrine/orm.svg)](LICENSE)

```
    ______                        ______             _
    | ___ \_                      | ___ \           | |
    | |_/ / \__ __   __  _ __   _ | |_/ /___   ___  | |
    |  __/|  _// _ \ \ \/ /| | | ||  __// _ \ / _ \ | |
    | |   | | | (_) | >  < \ |_| || |  | (_) | (_) || |___
    \_|   |_|  \___/ /_/\_\ \__  |\_|   \___/ \___/ \_____\
                           __ / /
                          /___ /
```

An automated, high-performance proxy pool for web scrapers and crawlers. It automatically fetches free public proxies, validates their availability on a scheduled basis, persists healthy proxies in Redis/SSDB, and exposes them via a lightweight RESTful API server.

---

## Key Features

- 🚀 **Production Ready for Cloud Free Tiers**: Optimized memory footprint (<300MB) for seamless deployment on **Google Cloud Compute Engine `e2-micro`** and **Oracle Cloud Always Free VM** instances.
- 🏡 **Residential IP Filtering**: Filter and fetch only residential proxies on-demand (`?residential=true` or `?type=residential`).
- 🔐 **Token-Based Authentication System**: Protect your API endpoints with a header-only, constant-time token check (`Authorization: Bearer <token>`, `X-API-Token`, `X-Auth-Token` or `Api-Key`).
- 🔒 **TLS Gateway**: The API serves **HTTPS on port `9443`** with a self-signed cert generated at deploy time (swap in a CA-signed cert any time) so the auth token is never sniffable in transit.
- 🛡️ **Zero-Log Requestor Privacy**: Strict privacy protection — no client IP addresses, headers, or requestor details are ever logged or retained in log files.
- ⚡ **Automated Scheduling & Validation**: Built-in APScheduler constantly checks proxy latency, availability, and failure thresholds.
- 🕒 **Fresh-Only Serving**: `/get` and `/all` return only proxies that **passed their last check** and were **re-validated within `PROXY_FRESH_SECONDS`** (default 900s), newest-checked first — never stale entries.
- 🔌 **Pluggable Architecture**: Modular proxy fetchers with automatic directory discovery and runtime hot-reloading.

---

## Quick Start & Local Setup

### Prerequisites
- Python 3.8+
- Redis Server (local or remote)

### Installation

```bash
# Clone the repository
git clone https://github.com/anand870/proxy_pool.git
cd proxy_pool

# Install dependencies
pip install -r requirements.txt
```

### Running Locally

```bash
# Generate the self-signed TLS gateway cert (once)
make gen-cert          # or: bash scripts/gen_gateway_cert.sh

# Start the proxy scheduler (fetcher & validator daemon)
python proxyPool.py schedule     # make scheduler

# Start the Web API server (HTTPS on :9443)
python proxyPool.py server       # make server
```

### Make Commands

A `Makefile` wraps the common local dev/ops tasks. Run `make help` for the list.
Override any variable inline, e.g. `make health TOKEN=abc PORT=9443`.

| Command | Description |
|---------|-------------|
| `make help` | List all available targets (default) |
| `make install` | Install runtime dependencies (`requirements.txt`) |
| `make install-dev` | Install runtime + test deps (`pytest`, `pytest-cov`, `fakeredis`) |
| `make gen-cert` | Generate the self-signed TLS gateway cert. Vars: `GATEWAY_DOMAIN=`, `EXTERNAL_IP=`, `FORCE=1` |
| `make server` | Run the API server (HTTPS on `:9443`) |
| `make scheduler` | Run the fetch/validate scheduler |
| `make fetchers` | List active proxy fetchers |
| `make test` | Run unit + API tests |
| `make test-all` | Run the full test suite |
| `make cov` | Run tests with a coverage report |
| `make health` | `GET /count/` against a running server (uses `--cacert gateway/tls.crt` + `TOKEN`) |
| `make get` | `GET /get/` against a running server |
| `make docker-up` / `make docker-down` | Build/start or stop the Docker Compose stack |
| `make deploy` | Remote-deploy to a GCP VM. Vars: `INSTANCE_NAME=`, `ZONE=`, env `AUTH_TOKEN`, `GATEWAY_DOMAIN` |
| `make clean` | Remove Python/test caches |
| `make clean-cert` | Remove the generated `gateway/tls.{crt,key}` |

`TOKEN` defaults to `AUTH_TOKEN` read from `.env` when present, so `make health` /
`make get` work with no arguments once the server is running.

---

## Production Deployment (Google Cloud `e2-micro`)

### Method 1: Deploy to Remote GCP VM from Local Machine (One-Command)

Run `remote_deploy.sh` directly from your local terminal. It will connect via SSH to your running GCP `e2-micro` VM, install `git` & dependencies, configure GCP firewall rules for port `9443`, pull code, and start the service:

```bash
# Basic usage (Target instance name: my-gcp-micro-instance, Zone: us-central1-a)
./remote_deploy.sh

# Deploy with custom instance name, zone, and secret AUTH_TOKEN:
INSTANCE_NAME="my-proxy-vm" ZONE="us-central1-a" AUTH_TOKEN="my_secret_token_123" ./remote_deploy.sh

# Optionally bind a real domain (adds it to the cert SAN):
INSTANCE_NAME="my-proxy-vm" AUTH_TOKEN="..." GATEWAY_DOMAIN="proxy.example.com" ./remote_deploy.sh
```

It opens the GCP firewall for `tcp:9443` and reports an `https://…:9443` URL.

### Method 2: Deploy Directly on Host Machine (Systemd)

On your GCP Compute Engine VM host instance, run the local deployment script:

```bash
chmod +x deploy.sh proxy_pool.sh
./deploy.sh
```
This script will:
1. Create a Python virtual environment (`venv`) and install dependencies.
2. Generate `.env` configuration template.
3. Install and register `proxy_pool.service` under `systemd`.
4. Start the production service via Gunicorn.

```bash
# Manage via systemd
sudo systemctl start proxy_pool
sudo systemctl status proxy_pool
sudo systemctl stop proxy_pool
sudo systemctl restart proxy_pool
```

### Checking Server Status & Logs

To verify if the server is running, check process logs, or inspect port binding:

- **Stream Live Logs**:
  ```bash
  sudo journalctl -u proxy_pool.service -f
  ```
- **View Recent Log History**:
  ```bash
  sudo journalctl -u proxy_pool.service -n 50 --no-pager
  ```
- **Check Service Health & Status**:
  ```bash
  sudo systemctl status proxy_pool
  ```
- **Verify Port 9443 Binding**:
  ```bash
  sudo lsof -i :9443
  ```
- **Smoke-test the HTTPS endpoint**:
  ```bash
  curl --cacert gateway/tls.crt -H "Authorization: Bearer $AUTH_TOKEN" https://127.0.0.1:9443/count/
  ```

### Method 3: Containerized Deployment (Docker & Docker Compose)

```bash
# Set your token in environment (optional)
export AUTH_TOKEN="my_secret_token_123"

# Generate the TLS gateway cert once (mounted into the container)
make gen-cert

# Build and launch with memory limits
docker-compose up -d
```

---

## Token Authentication

Set `AUTH_TOKEN` in your environment or `.env` file to enable token protection:

```ini
AUTH_TOKEN=my_secret_token_123
```

The token is read **from request headers only** and compared in constant time.
Query-string tokens (`?token=`) are **not** accepted — they leak into URLs, proxy
logs and referrers. Always run the API over HTTPS (see [TLS Gateway](#tls-gateway))
so the header cannot be sniffed in transit.

1. **HTTP Authorization Header** *(Recommended)*:
   ```bash
   curl --cacert gateway/tls.crt -H "Authorization: Bearer my_secret_token_123" "https://<SERVER_IP>:9443/get/"
   ```
2. **Custom Header** (`X-API-Token`, `X-Auth-Token` or `Api-Key`):
   ```bash
   curl --cacert gateway/tls.crt -H "X-API-Token: my_secret_token_123" "https://<SERVER_IP>:9443/get/"
   ```

*If the token is missing or invalid, the API responds with `HTTP 401 Unauthorized`.*

---

## TLS Gateway

The API server terminates TLS itself (via the embedded gunicorn) so the auth token
is never sent in cleartext. It listens on **HTTPS port `9443`** by default.

`deploy.sh` auto-generates a **self-signed** cert on first run
(`scripts/gen_gateway_cert.sh` → `gateway/tls.crt` + `gateway/tls.key`, RSA-2048,
10-year, SAN = `127.0.0.1` + the VM external IP + optional `GATEWAY_DOMAIN`).
Generate it manually with:

```bash
make gen-cert                       # localhost + auto-detected external IP
GATEWAY_DOMAIN=proxy.example.com make gen-cert
```

Clients must trust that cert — pass `--cacert gateway/tls.crt` to `curl`
(or `-k` to skip verification for a quick test).

**Switching to a CA-signed cert (Let's Encrypt etc.):** point a DNS name at the VM,
set `GATEWAY_DOMAIN` in `.env`, and drop the real `tls.crt` / `tls.key` into
`gateway/`. Restart the service — clients then need no `--cacert`.

`gateway/` and `.env` are git-ignored; the private key never leaves the host.

Set `SSL_ENABLED=false` to fall back to plain HTTP (not recommended).

---

## Residential IP Filtering & Count Parameter

Filter and fetch proxies marked as residential or datacenter IPs using `?residential=true|false`, or limit returned proxies using `?num=N`:

- **Fetch a random residential proxy**:
  ```bash
  curl "https://127.0.0.1:9443/get/?residential=true"
  ```
- **Fetch a random non-residential (datacenter) proxy**:
  ```bash
  curl "https://127.0.0.1:9443/get/?residential=false"
  ```
- **Pop and delete a residential proxy**:
  ```bash
  curl "https://127.0.0.1:9443/pop/?residential=true"
  ```
- **List residential proxies with quantity limit**:
  ```bash
  curl "https://127.0.0.1:9443/all/?residential=true&num=5"
  ```
- **List non-residential proxies**:
  ```bash
  curl "https://127.0.0.1:9443/all/?residential=false"
  ```
- **Proxy count statistics (including residential count)**:
  ```bash
  curl "https://127.0.0.1:9443/count/"
  # Response: {"http_type": {"http": 10, "https": 5}, "residential": 6, "source": {...}, "count": 15}
  ```

---

## Fresh-Only Proxy Serving

`/get`, `/pop`, `/all` and `/count` never expose stale proxies. A proxy is only
returned if **both** hold:

1. Its most recent validation **passed** (`last_status` is true).
2. It was re-validated within **`PROXY_FRESH_SECONDS`** (default `900`; set to `0`
   to disable the time window).

Results are ordered by check time, newest first. If no proxy currently falls
inside the freshness window, the API falls back to all still-passing proxies so
the pool never appears empty. The scheduler's own re-check job is unaffected — it
always iterates the full pool so failing/stale entries keep getting re-tested and
pruned.

---

## Zero-Log Requestor Privacy

To ensure complete requestor anonymity:
- **Werkzeug Logger**: Suppressed HTTP access logging of client IP addresses.
- **Gunicorn Server**: Configured with `accesslog = None` in production, ensuring client IP (`%(h)s`) and User-Agent (`%(a)s`) are never recorded or written to disk.

---

## RESTful API Reference

| Endpoint | Method | Description | Parameters |
|----------|--------|-------------|------------|
| `/` | GET | List available API routes | None |
| `/get` | GET | Get a random **freshly-validated** proxy | `type=https`, `residential=true|false` |
| `/pop` | GET | Get and delete a proxy | `type=https`, `residential=true|false` |
| `/all` | GET | Get **freshly-validated** proxies (newest-checked first) | `type=https`, `residential=true|false`, `num=N` |
| `/count` | GET | Get proxy count & statistics | None |
| `/delete` | GET | Delete an invalid proxy | `proxy=host:port` |

### Usage Example in Python (Scraper Integration)

```python
import requests

API_URL = "https://127.0.0.1:9443"
HEADERS = {"Authorization": "Bearer my_secret_token_123"}
# Self-signed gateway cert: point verify at gateway/tls.crt (or a real CA bundle).
VERIFY = "gateway/tls.crt"

def get_residential_proxy():
    response = requests.get(f"{API_URL}/get/", params={"residential": "true"}, headers=HEADERS, verify=VERIFY)
    return response.json().get("proxy")

def delete_proxy(proxy):
    requests.get(f"{API_URL}/delete/", params={"proxy": proxy}, headers=HEADERS, verify=VERIFY)

def fetch_target_page(url):
    retry_count = 5
    while retry_count > 0:
        proxy = get_residential_proxy()
        if not proxy:
            break
        try:
            resp = requests.get(url, proxies={"http": f"http://{proxy}", "https": f"http://{proxy}"}, timeout=10)
            if resp.status_code == 200:
                return resp.text
        except Exception:
            retry_count -= 1
            delete_proxy(proxy)
    return None
```

---

## Extending Proxy Sources

Create a new `.py` file in `fetcher/sources/` inheriting from `BaseFetcher`:

```python
from fetcher.baseFetcher import BaseFetcher
from util.webRequest import WebRequest

class CustomFetcher(BaseFetcher):
    name = "custom_fetcher"
    url = "https://www.example.com/"
    enabled = True
    is_residential = True  # Tag proxies from this source as residential

    def fetch(self):
        response = WebRequest().get("https://www.example.com/api/proxies")
        for item in response.json:
            yield f"{item['ip']}:{item['port']}"
```

The scheduler automatically scans `fetcher/sources/` on the next iteration and enables new fetchers without restarting the application.

### Auditing Source Health

`source_health.py` runs every source once, live-validates the proxies it returns,
and prints a per-source table (fetched / working / rate) plus overlap between
sources. It writes a JSON dump under `log/`.

```bash
python source_health.py                # all sources
python source_health.py scdn iplocate  # only named sources
python source_health.py --no-validate  # fetch only, skip validation
```

---

## Supported Public Proxy Sources

| Source Name | Enabled | Residential Tag | File Path |
|-------------|---------|-----------------|-----------|
| IPLocate | ✔ | No | [`iplocate.py`](fetcher/sources/iplocate.py) |
| RoundProxies | ✔ | Yes | [`roundproxies.py`](fetcher/sources/roundproxies.py) |
| Proxifly | ✔ | No | [`proxifly.py`](fetcher/sources/proxifly.py) |
| SCDN | ✔ | No | [`scdn.py`](fetcher/sources/scdn.py) |
| Kxdaili | ✔ | No | [`kxdaili.py`](fetcher/sources/kxdaili.py) |
| IP3366 | ✔ | No | [`ip3366.py`](fetcher/sources/ip3366.py) |
| Ihuan | ✔ | No | [`ihuan.py`](fetcher/sources/ihuan.py) |
| IP89 | ✔ | No | [`ip89.py`](fetcher/sources/ip89.py) |
| Daili66 | ✔ | No | [`daili66.py`](fetcher/sources/daili66.py) |
| FreeVPNNode | ✔ | No | [`freevpnnode.py`](fetcher/sources/freevpnnode.py) |
| Geonode | ✗ Disabled | Yes | [`geonode.py`](fetcher/sources/geonode.py) |
| Kuaidaili | ✗ Disabled | No | [`kuaidaili.py`](fetcher/sources/kuaidaili.py) |
| DocIP | ✗ Disabled | No | [`docip.py`](fetcher/sources/docip.py) |
| GoodIPs | ✗ Disabled | No | [`goodips.py`](fetcher/sources/goodips.py) |
| Zdaye | ✗ Disabled | No | [`zdaye.py`](fetcher/sources/zdaye.py) |

> Sources are marked **Disabled** (`enabled = False`, file retained) when the
> upstream site is down or its response format broke: `docip` (site offline),
> `geonode` (empty API), `zdaye` / `kuaidaili` / `goodips` (parser / anti-bot
> failures). Flip `enabled` back to `True` to re-activate once fixed.

---

## Configuration Reference (`setting.py` / `.env`)

| Variable | Default | Description |
|----------|---------|-------------|
| `HOST` | `0.0.0.0` | API server binding address |
| `PORT` | `9443` | API server port (HTTPS) |
| `AUTH_TOKEN` | `""` | API token authentication (empty = disabled) |
| `SSL_ENABLED` | `true` | Serve HTTPS using `gateway/tls.crt` + `gateway/tls.key` |
| `SSL_CERTFILE` | `gateway/tls.crt` | TLS cert path (relative to project root or absolute) |
| `SSL_KEYFILE` | `gateway/tls.key` | TLS private key path |
| `GATEWAY_DOMAIN` | `""` | Optional DNS name added to the generated cert's SAN |
| `DB_CONN` | `redis://:pwd@127.0.0.1:6379/0` | DB connection string (Redis or SSDB) |
| `TABLE_NAME` | `use_proxy` | Database table / hash key name |
| `GUNICORN_WORKERS` | `2` | Gunicorn worker processes (optimized for 1GB RAM) |
| `GUNICORN_THREADS` | `2` | Threads per Gunicorn worker |
| `VERIFY_TIMEOUT` | `10` | Proxy validation timeout in seconds |
| `POOL_SIZE_MIN` | `20` | Minimum proxy threshold before triggering re-fetch |
| `PROXY_FRESH_SECONDS` | `900` | Max age (seconds) since last successful check for a proxy to be served by `/get` & `/all`; `0` disables the time filter |
| `TIMEZONE` | `Asia/Shanghai` | Scheduler timezone |

---

## Running Tests

```bash
# Run unit & API test suite
pytest

# View coverage report
pytest --cov=. --cov-report=term-missing
```

---

## License

Distributed under the MIT License. See [LICENSE](LICENSE) for details.
