# Project Provenance

## Source & Author
- **Application Name:** CampusDesk (IT Helpdesk & Equipment Request Portal)
- **Author:** Student Submission (CS-303 Software Vulnerabilities, Winter 2026)
- **License:** MIT License
- **Original Repository:** Created specifically for the CS-303 capstone vulnerability assessment project.

## How It Was Made
- **Creation Method:** AI-generated base application with manual configuration and review, following the "First choice: generate one" project brief workflow in CS-303.
- **Tool & Model Version:** Google Gemini (Gemini 2.5 Pro, October 2026).

## Modifications & Setup
- Configured Docker and `docker-compose.yml` to bind strictly to `127.0.0.1:8000` for safe local testing.
- Pinned third-party Python dependencies in `requirements.txt`.
- Added initial SQLite database schema and synthetic seed data (`schema_and_seed.sql`) with test accounts (`alice`, `bob`, `staff_marco`, `admin`) so the application starts with a single command and can be inspected immediately.