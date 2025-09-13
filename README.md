# ATIcketing — Django + DRF + PostgreSQL (ready)

Prototipo **Python/Django** configurato **direttamente con PostgreSQL**.
Include `docker-compose` (Postgres + MailHog) e login + dashboard per ruolo.

## Avvio con Docker (consigliato)
```bash
# nella cartella ATIcketing
docker compose up -d --build
# Primo setup (dentro il container web)
docker compose exec web python manage.py migrate
docker compose exec web python manage.py createsuperuser
docker compose exec web python manage.py seed_initial
```
- App: http://127.0.0.1:8000/
- MailHog (email di prova): http://127.0.0.1:8025

## Avvio locale (senza Docker)
1) Installa PostgreSQL 14+ e crea un DB/utente:
   - DB: `aticketing`  - user: `postgres`  - pass: `postgres`  - host: `localhost`  - port: `5432`
2) Crea venv e dipendenze:
```bash
python -m venv .venv
# Windows: .venv\Scripts\activate
# Linux/Mac: source .venv/bin/activate
pip install -r requirements.txt
```
3) Configura l'ENV:
```bash
cp .env.example .env
# se usi SMTP dev, facoltativo: docker run -p 1025:1025 -p 8025:8025 mailhog/mailhog
```
4) Migrazioni e seed:
```bash
python manage.py migrate
python manage.py createsuperuser
python manage.py seed_initial
python manage.py runserver 0.0.0.0:8000
```
- Login: http://127.0.0.1:8000/ (smistamento a dashboard per ruolo)
- Admin: http://127.0.0.1:8000/admin
- API: http://127.0.0.1:8000/api/
- MailHog: http://127.0.0.1:8025

## Flusso ruoli
- Gruppi: **Admin**, **SuperUser**, **Coordinatore**, **Operatore** (creati dal seed).
- Dopo login:
  - Admin/SuperUser/Coordinatore → `/dash/team/`
  - Operatore → `/dash/operator/`

## Note
- Email: con `MAILHOG` configurato in `.env.docker`, tutte le email vanno su http://127.0.0.1:8025
- Protocollo: `ICT|WH|SP-YYYY-WW-NNNN` con progressivo **per settimana e comparto** (transazione con row-lock PostgreSQL).

## Riavvio pulito con Docker
```bash
# dopo aver fatto
docker compose down
# nella cartella ATIcketing,
# Avvia DB e MailHog
docker compose up -d --build db mailhog
#verifica che DB sia healthy
docker compose ps
# Migrazioni + seed con container “one-off”. 
# Usa questi solo se parti da DB vuoto o se non li avevi già fatti.
docker compose run --rm web python manage.py migrate
docker compose run --rm web python manage.py createsuperuser
docker compose run --rm web python manage.py seed_initial
# Avvio servizio web
docker compose up -d web
# Check rapido
docker compose ps
docker compose logs --tail=80 web

# Se fai modifiche al codice
docker compose restart web
