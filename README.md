<p align="center" style="display: flex; align-items: center; justify-content: center; gap: 10px;">
  <img width="170" height="170" alt="image" src="https://github.com/user-attachments/assets/5db2afc3-e0b6-437b-867f-7fe7da9f98bc" />
  <img width
  <img width="140" height="140" alt="image" src="https://github.com/user-attachments/assets/04ac913f-1fa3-4ace-af1a-e6b3f8d3adc3" />  
</p>
<h1>DocConvert</h1>


A scalable document conversion platform built on microservices — upload, convert, and download documents through secure, async APIs.

---

## Architecture

```
Client
  └─► API Gateway (Auth + Rate Limiting)
        └─► Upload Service → S3
              └─► RabbitMQ
                    ├─► Conversion Workers → S3
                    └─► Status Service → PostgreSQL
                              └─► Download Service
```

---

## Features

- **Auth** — JWT, API Keys, OAuth2, scope-based + role-based access control
- **Rate Limiting** — per user plan, API key, and role
- **Async Processing** — RabbitMQ job queue with scalable conversion workers
- **Formats** — PDF, DOCX, XLSX, TXT, and more
- **Storage** — S3-compatible object storage
- **Observability** — Prometheus metrics + structured logging

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Backend | Python, FastAPI |
| Queue | RabbitMQ |
| Database | PostgreSQL, SQLAlchemy |
| Storage | S3-compatible |
| Auth | JWT, OAuth2, API Keys |
| DevOps | Docker, Docker Compose, Prometheus |

---

## Getting Started

**Prerequisites:** Docker, Docker Compose

```bash
git clone https://github.com/charantm7/docconvert-platform.git
cd docconvert-platform
docker compose up --build
```

This starts all services: API Gateway, Upload, Conversion Workers, RabbitMQ, PostgreSQL, and Prometheus.

---

## Services

| Service | Responsibility |
|---------|---------------|
| `api_gateway` | Entry point — auth & rate limiting |
| `upload_service` | Accepts and stores uploaded documents |
| `conversion_workers` | Processes conversion jobs from queue |
| `status_service` | Tracks and exposes job progress |
| `download_service` | Serves converted files |

---

## How It Works

1. User uploads a document → stored in S3
2. Conversion job published to RabbitMQ
3. Worker picks up job, converts the file, saves result to S3
4. Status service updates job state in PostgreSQL
5. User polls status and downloads the converted file

---

## Monitoring

Prometheus is preconfigured via `prometheus.yml`. Extend with Grafana and Alertmanager as needed.

---

## Roadmap

- [ ] Web dashboard
- [ ] Additional format support
- [ ] Worker autoscaling
- [ ] Webhooks for job completion
- [ ] Grafana dashboards
- [ ] Multi-tenant support

---

## Contributing

```bash
# 1. Fork the repo
# 2. Create a feature branch
git checkout -b feature/your-feature
# 3. Commit and push
git commit -m "add: your feature"
git push origin feature/your-feature
# 4. Open a Pull Request
```

---

## License

MIT © [Charan TM](https://github.com/charantm7)
