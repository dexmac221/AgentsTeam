FastAPI System Monitor provides a simple yet powerful interface for collecting and visualizing system metrics. It is ideal for:
- DevOps teams needing quick insights into server health
- CI/CD pipelines that require automated health checks
- Microservice architectures that need lightweight monitoring

The application is containerized, supports environment-based configuration, and can be extended with custom metrics or alerting hooks.

<!-- Features -->

- Real-time CPU, memory, disk, and network statistics
- JSON and Prometheus-compatible endpoints
- Configurable polling intervals via environment variables
- Docker-ready with a pre-built image
- Automatic OpenAPI documentation
- Graceful shutdown handling

<!-- Installation -->

git clone https://github.com/yourusername/fastapi-system-monitor.git
cd fastapi-system-monitor

python -m venv .venv
source .venv/bin/activate  # On Windows use `.venv\Scripts\activate`

pip install -r requirements.txt

<!-- Docker -->

docker build -t fastapi-system-monitor .

docker run -d --name system-monitor -p 8000:8000 fastapi-system-monitor

<!-- Configuration -->


POLL_INTERVAL=5

PROMETHEUS_ENABLED=true

LOG_LEVEL=INFO

HOST=0.0.0.0
PORT=8000

All variables are optional; defaults are provided in the code.

<!-- Usage -->



GET /metrics

Response:

{
  "cpu_percent": 12.5,
  "memory": {
    "total": 16777216,
    "available": 12345678,
    "used": 4444444,
    "percent": 26.5
  },
  "disk": {
    "total": 500000000,
    "used": 200000000,
    "free": 300000000,
    "percent": 40.0
  },
  "network": {
    "bytes_sent": 123456,
    "bytes_recv": 654321
  }
}


GET /metrics/prometheus

The endpoint exposes metrics in Prometheus exposition format.


Navigate to `http://localhost:8000/docs` for interactive API documentation.

<!-- Troubleshooting -->


<!-- Screenshots -->

- **OpenAPI UI**: The interactive Swagger UI displays all available endpoints and allows you to test them directly from the browser.
- **Prometheus Metrics**: A plain text view of the metrics exposed for scraping by Prometheus.

<!-- Contribution -->

Feel free to open issues or submit pull requests. Please follow the existing coding style and add tests for new features.

<!-- License -->

MIT License. See `LICENSE` file for details.