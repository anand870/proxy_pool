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
- 🔐 **Token-Based Authentication System**: Protect your API endpoints with configurable token authentication (`Authorization: Bearer <token>`, `X-API-Token`, or `?token=<token>`).
- 🛡️ **Zero-Log Requestor Privacy**: Strict privacy protection — no client IP addresses, headers, or requestor details are ever logged or retained in log files.
- ⚡ **Automated Scheduling & Validation**: Built-in APScheduler constantly checks proxy latency, availability, and failure thresholds.
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
# Start the proxy scheduler (fetcher & validator daemon)
python proxyPool.py schedule

# Start the Web API server
python proxyPool.py server
```

---

## Production Deployment (Google Cloud `e2-micro`)

### Method 1: Deploy to Remote GCP VM from Local Machine (One-Command)

Run `remote_deploy.sh` directly from your local terminal. It will connect via SSH to your running GCP `e2-micro` VM, install `git` & dependencies, configure GCP firewall rules for port `5010`, pull code, and start the service:

```bash
# Basic usage (Target instance name: my-gcp-micro-instance, Zone: us-central1-a)
./remote_deploy.sh

# Deploy with custom instance name, zone, and secret AUTH_TOKEN:
INSTANCE_NAME="my-proxy-vm" ZONE="us-central1-a" AUTH_TOKEN="my_secret_token_123" ./remote_deploy.sh
```

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
- **Verify Port 5010 Binding**:
  ```bash
  sudo lsof -i :5010
  ```

### Method 3: Containerized Deployment (Docker & Docker Compose)

```bash
# Set your token in environment (optional)
export AUTH_TOKEN="my_secret_token_123"

# Build and launch with memory limits
docker-compose up -d
```

---

## Token Authentication

Set `AUTH_TOKEN` in your environment or `.env` file to enable token protection:

```ini
AUTH_TOKEN=my_secret_token_123
```

When enabled, API requests must include the token via any of the following 3 formats:

1. **HTTP Authorization Header** *(Recommended)*:
   ```bash
   curl -H "Authorization: Bearer my_secret_token_123" "http://<SERVER_IP>:5010/get/"
   ```
2. **Custom Header**:
   ```bash
   curl -H "X-API-Token: my_secret_token_123" "http://<SERVER_IP>:5010/get/"
   ```
3. **URL Query Parameter**:
   ```bash
   curl "http://<SERVER_IP>:5010/get/?token=my_secret_token_123"
   ```

*If the token is missing or invalid, the API responds with `HTTP 401 Unauthorized`.*

---

## Residential IP Filtering & Count Parameter

Filter and fetch proxies marked as residential or datacenter IPs using `?residential=true|false`, or limit returned proxies using `?num=N`:

- **Fetch a random residential proxy**:
  ```bash
  curl "http://127.0.0.1:5010/get/?residential=true"
  ```
- **Fetch a random non-residential (datacenter) proxy**:
  ```bash
  curl "http://127.0.0.1:5010/get/?residential=false"
  ```
- **Pop and delete a residential proxy**:
  ```bash
  curl "http://127.0.0.1:5010/pop/?residential=true"
  ```
- **List residential proxies with quantity limit**:
  ```bash
  curl "http://127.0.0.1:5010/all/?residential=true&num=5"
  ```
- **List non-residential proxies**:
  ```bash
  curl "http://127.0.0.1:5010/all/?residential=false"
  ```
- **Proxy count statistics (including residential count)**:
  ```bash
  curl "http://127.0.0.1:5010/count/"
  # Response: {"http_type": {"http": 10, "https": 5}, "residential": 6, "source": {...}, "count": 15}
  ```

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
| `/get` | GET | Get a random proxy | `type=https`, `residential=true|false` |
| `/pop` | GET | Get and delete a proxy | `type=https`, `residential=true|false` |
| `/all` | GET | Get proxies from pool | `type=https`, `residential=true|false`, `num=N` |
| `/count` | GET | Get proxy count & statistics | None |
| `/delete` | GET | Delete an invalid proxy | `proxy=host:port` |

### Usage Example in Python (Scraper Integration)

```python
import requests

API_URL = "http://127.0.0.1:5010"
HEADERS = {"Authorization": "Bearer my_secret_token_123"}

def get_residential_proxy():
    response = requests.get(f"{API_URL}/get/", params={"residential": "true"}, headers=HEADERS)
    return response.json().get("proxy")

def delete_proxy(proxy):
    requests.get(f"{API_URL}/delete/", params={"proxy": proxy}, headers=HEADERS)

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

---

## Supported Public Proxy Sources

| Source Name | Enabled | Residential Tag | File Path |
|-------------|---------|-----------------|-----------|
| Geonode | ✔ | Yes | [`geonode.py`](fetcher/sources/geonode.py) |
| RoundProxies | ✔ | Yes | [`roundproxies.py`](fetcher/sources/roundproxies.py) |
| Proxifly | ✔ | No | [`proxifly.py`](fetcher/sources/proxifly.py) |
| Kuaidaili | ✔ | No | [`kuaidaili.py`](fetcher/sources/kuaidaili.py) |
| Kxdaili | ✔ | No | [`kxdaili.py`](fetcher/sources/kxdaili.py) |
| IP3366 | ✔ | No | [`ip3366.py`](fetcher/sources/ip3366.py) |
| Ihuan | ✔ | No | [`ihuan.py`](fetcher/sources/ihuan.py) |
| IP89 | ✔ | No | [`ip89.py`](fetcher/sources/ip89.py) |
| DocIP | ✔ | No | [`docip.py`](fetcher/sources/docip.py) |
| GoodIPs | ✔ | No | [`goodips.py`](fetcher/sources/goodips.py) |
| Daili66 | ✔ | No | [`daili66.py`](fetcher/sources/daili66.py) |
| FreeVPNNode | ✔ | No | [`freevpnnode.py`](fetcher/sources/freevpnnode.py) |

---

## Configuration Reference (`setting.py` / `.env`)

| Variable | Default | Description |
|----------|---------|-------------|
| `HOST` | `0.0.0.0` | API server binding address |
| `PORT` | `5010` | API server port |
| `AUTH_TOKEN` | `""` | API token authentication (empty = disabled) |
| `DB_CONN` | `redis://:pwd@127.0.0.1:6379/0` | DB connection string (Redis or SSDB) |
| `TABLE_NAME` | `use_proxy` | Database table / hash key name |
| `GUNICORN_WORKERS` | `2` | Gunicorn worker processes (optimized for 1GB RAM) |
| `GUNICORN_THREADS` | `2` | Threads per Gunicorn worker |
| `VERIFY_TIMEOUT` | `10` | Proxy validation timeout in seconds |
| `POOL_SIZE_MIN` | `20` | Minimum proxy threshold before triggering re-fetch |
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
