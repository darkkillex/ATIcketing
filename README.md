# ATIcketing — Django + DRF + PostgreSQL

Prototipo **Python/Django** configurato **direttamente con PostgreSQL**.  
Include login con smistamento per ruolo, dashboard, allegati, export CSV, timeline/audit ed API REST.

---

## Panoramica
Ticketing aziendale con ruoli **Admin/SuperUser/Coordinatore/Operatore**, protocolli automatici per comparto (ICT/WH/SP), notifiche email, filtri avanzati e audit completo delle attività.

> **Obiettivo:** prototipo manutenibile e pronto per rollout su server in rete locale.

---

## Stack
- **Backend:** Django 5, Django REST Framework
- **DB:** PostgreSQL
- **Email (dev):** MailHog
- **UI:** Materialize CSS
- **CORS:** `django-cors-headers` (aperto in DEBUG, whitelist in PROD)
- **Allegati:** filesystem locale (MEDIA_ROOT)

---

## Requisiti
- Docker & Docker Compose (consigliato)
- In alternativa: Python 3.11 + PostgreSQL 14+

---

## Avvio con Docker (consigliato)

### Quick start
```bash
# nella cartella ATIcketing
docker compose up -d --build

# primo setup
docker compose exec web python manage.py migrate
docker compose exec web python manage.py createsuperuser
docker compose exec web python manage.py seed_initial
```

- App: <http://127.0.0.1:8000/>
- MailHog (email di prova): <http://127.0.0.1:8025>

### Riavvio pulito
```bash
# spegni tutto
docker compose down

# avvia solo DB + MailHog (opzionale)
docker compose up -d --build db mailhog

# controlla stato
docker compose ps

# migrazioni/seed (se DB vuoto)
docker compose run --rm web python manage.py migrate
docker compose run --rm web python manage.py createsuperuser
docker compose run --rm web python manage.py seed_initial

# avvia servizio web
docker compose up -d web

# verifica
docker compose ps
docker compose logs --tail=80 web

# dopo modifiche al codice
docker compose restart web
```

---

## Avvio locale (senza Docker)
1) Installa PostgreSQL 14+ e crea un DB/utente:
   - DB: `aticketing` · user: `postgres` · pass: `postgres` · host: `localhost` · port: `5432`
2) Crea venv e installa dipendenze:
```bash
python -m venv .venv
# Windows: .venv\Scripts\activate
# Linux/Mac: source .venv/bin/activate
pip install -r requirements.txt
```
3) Configura l’ENV:
```bash
cp .env.example .env
# (opzionale) SMTP dev: docker run -p 1025:1025 -p 8025:8025 mailhog/mailhog
```
4) Migrazioni e seed:
```bash
python manage.py migrate
python manage.py createsuperuser
python manage.py seed_initial
python manage.py runserver 0.0.0.0:8000
```
- Login: <http://127.0.0.1:8000/> (smistamento a dashboard per ruolo)  
- Admin: <http://127.0.0.1:8000/admin>  
- API: <http://127.0.0.1:8000/api/>  
- MailHog: <http://127.0.0.1:8025>

---

## Configurazione (.env)
Variabili principali (dev/prod):
```env
# Django
DJANGO_SECRET_KEY=...
DJANGO_DEBUG=True
DJANGO_ALLOWED_HOSTS=localhost,127.0.0.1

# DB
DB_HOST=db
DB_PORT=5432
DB_NAME=aticketing
DB_USER=postgres
DB_PASSWORD=postgres

# Email (dev con MailHog)
EMAIL_HOST=mailhog
EMAIL_PORT=1025
EMAIL_USE_TLS=False

# CORS/CSRF (solo PROD)
CORS_ALLOWED_ORIGINS=https://intranet.lan,https://portal.lan
CSRF_TRUSTED_ORIGINS=https://intranet.lan,https://portal.lan

# URL base per link nelle email
SITE_BASE_URL=http://127.0.0.1:8000
DEFAULT_FROM_EMAIL=ATIcketing <no-reply@local>
```
> In **DEBUG=True**: CORS è aperto a tutti, nessuna variabile necessaria.  
> In **PROD**: imposta `DJANGO_ALLOWED_HOSTS`, `CORS_ALLOWED_ORIGINS` e, se servono cookie cross-site, `CSRF_TRUSTED_ORIGINS` **con schema** (`http://` o `https://`).

---

## Flusso & rotte principali
- **Login:** `/accounts/login/`
- **Landing:** `/` → redirect automatico a dashboard coerente col ruolo
- **Dashboard Operatore:** `/dash/operator/`
- **Dashboard Team (staffish):** `/dash/team/`
- **Nuovo Ticket:** `/tickets/new/`
- **Dettaglio Ticket:** `/tickets/<id>/`
- **Export CSV:** `/tickets/operator.csv`, `/tickets/team.csv` (rispettano i filtri attivi)
- **Audit CSV (singolo ticket):** `/tickets/<id>/audit.csv`

**Nomi URL (per template):**  
`landing`, `dash_operator`, `dash_team`, `ticket_new`, `ticket_detail`, `operator_export_csv`, `team_export_csv`, `ticket_audit_csv`.

---

## Ruoli & permessi
- Gruppi: **Admin**, **SuperUser**, **Coordinatore**, **Operatore** (creati dal `seed_initial`).
- Dopo login:
  - Admin / SuperUser / Coordinatore → `/dash/team/`
  - Operatore → `/dash/operator/`

Controllo centralizzato in `tickets/permissions.py` (`is_staffish`, `TicketPermissions`).

---

## Protocolli & reparti
Formato protocollo: `ICT|WH|SP-YYYY-WW-NNNN`, con progressivo **per settimana e comparto** (transazione con row-lock PostgreSQL).

Emails reparto (`settings.TICKET_DEPARTMENT_EMAILS`):
```python
{
  'ICT': 'ati.ict@sivam.com',
  'WH':  'ati.magazzino@sivam.com',
  'SP':  'ati.pianoturni@sivam.com',
}
```

---

## Funzionalità principali
- Creazione ticket con allegati multipli
- RBAC: Operatore vs Staff (Admin/SuperUser/Coordinatore)
- Filtri, ricerca libera `q`, paginazione, page size e “Solo miei” (in Team)
- Notifiche email (nuovo ticket, cambio stato, commento pubblico, nuovi allegati)
- Timeline/Audit (CREATED, STATUS_CHANGED, COMMENT_ADDED, ATTACHMENT_ADDED)
- Export CSV (operator/team) e **export audit** del singolo ticket

---

## API (DRF)
- Endpoint: `/api/` (autenticazione richiesta — sessione o token se abilitato)
- Esempio lettura tickets autenticata via sessione (browser DRF)
- Rate limit (default): anon `60/min`, user `600/min` (configurabili via env)

> Se abiliti i token DRF o usi librerie dedicate (es. djoser), documenta qui i relativi endpoint.

---

## Filtri & querystring nei link
Il templatetag `{% url_replace %}` mantiene la querystring su link/paginazione/export.  
File: `tickets/templatetags/querystring.py`.

Esempio:
```django
{% load querystring %}
<a href="{% url 'team_export_csv' %}{% url_replace %}">CSV</a>
```

---

## 404/500 eleganti (prod)
Aggiungi `templates/404.html` (e facoltativi `500.html`, `403.html`).  
Test 404 in locale: imposta `DJANGO_DEBUG=False` + `DJANGO_ALLOWED_HOSTS=127.0.0.1,localhost`, riavvia, apri un URL inesistente.

---

## Troubleshooting
- **NoReverseMatch `dash_team_export`** → aggiorna i template a `team_export_csv` (o mantieni alias in `urls.py`).
- **`ModuleNotFoundError: corsheaders`** → aggiungi a `requirements.txt` e ricostruisci l’immagine: `docker compose up -d --build web`.
- **`ClearableFileInput doesn't support uploading multiple files`** → gestisci gli allegati multipli in view (già fatto), evita `ClearableFileInput(multiple=True)`.
- **Root 404** → esiste la view `landing` su `/` che redireziona in base al ruolo. In produzione usa `templates/404.html` per gli altri 404.

---

## Testing
```bash
docker compose run --rm web pytest
```

---

## Changelog
- v0.2.x — Filtri/paginazione, email templatizzate, audit, export CSV, miglioramenti UI
- v0.1.x — MVP ticketing, protocolli reparto, notifiche base

---

## Licenza
Proprietario (uso interno).

