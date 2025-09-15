# ATIcketing — Django 5 + DRF + PostgreSQL

Helpdesk **Django** con **REST API**, allegati, audit/timeline, notifiche email templated e UI **mobile‑first** (MaterializeCSS).  
Pronto per sviluppo in Docker e deploy on‑prem (prod LAN).

---

## ⚡️ Avvio rapido con Docker (consigliato)

```bash
# nella cartella di progetto
docker compose up -d --build

# Primo setup DB
docker compose exec web python manage.py migrate
docker compose exec web python manage.py createsuperuser
docker compose exec web python manage.py seed_initial
```

- App: <http://127.0.0.1:8000/>
- MailHog (email di prova): <http://127.0.0.1:8025>

> Gli **allegati** in dev sono serviti direttamente da Django (vedi sezione “Media”).

---

## 💻 Avvio locale (senza Docker)

1) Installa PostgreSQL 14+ e crea un DB/utente:
   - DB: `aticketing` — user: `postgres` — pass: `postgres` — host: `localhost` — port: `5432`

2) Crea venv e dipendenze:
```bash
python -m venv .venv
# Windows: .venv\Scripts\activate
# Linux/Mac: source .venv/bin/activate
pip install -r requirements.txt
```

3) Configura l’ENV:
```bash
cp .env.example .env
# opzionale per email di test: docker run -p 1025:1025 -p 8025:8025 mailhog/mailhog
```

4) Migrazioni & seed:
```bash
python manage.py migrate
python manage.py createsuperuser
python manage.py seed_initial
python manage.py runserver 0.0.0.0:8000
```

- App: <http://127.0.0.1:8000/>  
- Admin: <http://127.0.0.1:8000/admin>  
- API: <http://127.0.0.1:8000/api/>  
- MailHog: <http://127.0.0.1:8025>

---

## 🔐 Ruoli & flusso

Seed iniziale crea i gruppi: **Admin**, **SuperUser**, **Coordinatore**, **Operatore**.

- Dopo login:  
  - Staff (Admin/SuperUser/Coordinatore) → `/dash/team/`  
  - Operatore → `/dash/operator/`

Permessi lato UI/API basati su helper `is_staffish(user)`.

---

## 🧩 Funzionalità principali

- **Ticket** con protocollo per comparto/settimana, campi (priorità, impatto, urgenza, canale, location, asset)
- **Commenti** (pubblici + interni) e **allegati multipli**
- **Timeline/Audit** (create, change status, commenti, allegati, assegnazioni)
- **Filtri & paginazione** su dashboard (testo, stato, priorità, reparto, range date, page size, “solo miei” lato team)
- **Notifiche email** (nuovo ticket, cambio stato, nuovo commento pubblico, nuovi allegati) con **template HTML**
- **Export CSV** coerente coi filtri (operator/team)
- **REST API** via DRF (Session/TokenAuth), throttling, CORS di sviluppo
- **UI mobile‑first**: navbar responsiva, filtri a griglia, tabelle scorrevoli, form ottimizzati

---

## 🗂️ Media (allegati)

- Path: `MEDIA_ROOT = <proj>/media`  → file in `media/attachments/YYYY/WW/...`
- URL: `MEDIA_URL = /media/`

### Dev (Django serve i media)
In `ATIcketing/urls.py` è presente l’handler statico dei media **in debug**. Se vuoi servirli anche con `DEBUG=False` durante lo sviluppo locale, puoi attivare l’“Opzione A” (già applicata nel progetto): mappatura `MEDIA_URL` -> `MEDIA_ROOT` tramite `static()` così da rendere scaricabili i file anche senza Nginx.

> **Nota:** in **produzione** è consigliato lasciare `DEBUG=False` e far servire `/media/` da **Nginx**, non da Django. Vedi “Produzione (LAN)”.

**Verifiche rapide se il download fallisce:**
1. Il file esiste sul filesystem? (`media/attachments/...`)
2. `MEDIA_URL` è corretto e compare in pagina come link `/media/...`?
3. In dev: la URL è mappata in `urls.py` (sezione `static(settings.MEDIA_URL, ...)`)?
4. In Docker: il volume `./media:/app/media` è montato nel servizio `web`?

---

## ✉️ Email

- In dev usa **MailHog** (già in `docker-compose.yml`): SMTP host `mailhog:1025`, web UI su `http://127.0.0.1:8025`.
- Config sensibili in `.env` / `.env.docker`:
  - `EMAIL_HOST`, `EMAIL_PORT`, `EMAIL_HOST_USER`, `EMAIL_HOST_PASSWORD`, `EMAIL_USE_TLS`
- Mittente: `DEFAULT_FROM_EMAIL` (default: `ATIcketing <no-reply@local>`)
- Link nelle mail: `SITE_BASE_URL` (default: `http://127.0.0.1:8000`)
- Routing reparti: `TICKET_DEPARTMENT_EMAILS` in `settings.py` (es. ICT/WH/SP)

---

## ⚙️ Configurazione (ENV)

Usa **.env.example** come base. Con Docker, variabili in **.env.docker** via `env_file`.

Chiavi utili:
- `DJANGO_SECRET_KEY`, `DJANGO_DEBUG`, `DJANGO_ALLOWED_HOSTS`
- `DB_*` (NAME, USER, PASSWORD, HOST, PORT)
- `SITE_BASE_URL`, `DEFAULT_FROM_EMAIL`
- **CORS/CSRF** (per prod):  
  - `CORS_ALLOWED_ORIGINS=https://intranet.lan,https://portal.lan`  
  - `CSRF_TRUSTED_ORIGINS=https://intranet.lan,https://portal.lan`

> In dev (`DJANGO_DEBUG=True`) CORS è **liberale** (allow all).

### Esempio PROD (LAN)
```
DJANGO_DEBUG=False
DJANGO_ALLOWED_HOSTS=aticketing.lan,10.0.0.20

CORS_ALLOWED_ORIGINS=https://intranet.lan,https://portal.lan
CSRF_TRUSTED_ORIGINS=https://intranet.lan,https://portal.lan

SITE_BASE_URL=https://aticketing.lan
DEFAULT_FROM_EMAIL=ATIcketing <no-reply@aticketing.lan>
```

> Valori di CORS/CSRF **devono** includere lo schema (`http://` o `https://`).

---

## 🔗 URL principali

UI
- `/` → redirect a dashboard corretta per ruolo
- `/dash/operator/` e `/dash/team/`
- `/tickets/new/`, `/tickets/<pk>/`
- Export CSV: `/tickets/operator.csv`, `/tickets/team.csv`
- Audit CSV (singolo ticket): `/tickets/<pk>/audit.csv`

API (DRF Router)
- `/api/tickets/` (autenticazione `TokenAuthentication` o `SessionAuthentication`)
- Throttling: `anon` `60/min`, `user` `600/min` (override via env).

Error pages
- **Custom** `403.html`, `404.html`, `500.html` (navbar “soft”, niente doppio login; se autenticato mostra link alla dashboard).

---

## 🧪 Test (WIP)
- Da completare: unit test per servizi, permission e viste.  
- CI suggerita: GitHub Actions con matrix (py 3.11/3.12) e PostgreSQL di servizio.

---

## 🚀 Produzione (LAN) — schema suggerito

- `DEBUG=False`
- **Gunicorn** per Django (app WSGI)
- **Nginx** davanti:
  - reverse proxy su Gunicorn per `location /`
  - **serve `/media/`** direttamente dal filesystem (volume o path condiviso)
- Statici (se necessario): `collectstatic` e Nginx `location /static/`

Snippet Nginx indicativo per media:
```nginx
location /media/ {
    alias /opt/aticketing/media/;  # deve puntare a MEDIA_ROOT
    autoindex off;
    add_header X-Content-Type-Options nosniff;
}
```

---

## 🧾 Changelog (estratto)

- **v0.6.0** — UI **mobile‑first** (navbar responsiva, filtri in griglia, tabelle scorrevoli), miglior UX date e form.
- **v0.5.x** — Timeline/audit, export CSV, filtri & ricerca, notifiche email templated, RBAC, API hardening.

---

## 🛟 Troubleshooting rapido

**Non riesco a scaricare gli allegati**
- Verifica la presenza del file in `media/attachments/...`
- Assicurati che la URL del link inizi con `/media/`
- In dev: conferma la mappatura in `urls.py` (static per MEDIA_URL)
- In Docker: controlla che `./media` sia montato nel container web

**Il logout non funziona**
- Il link deve puntare a `{% url 'logout' %}` e la route esiste in `urls.py` (Django `LogoutView`).

**La 404 custom non si vede**
- Serve `DEBUG=False` e riavvio container; gli handler `handler404/403/500` devono essere registrati in `ATIcketing/urls.py`.

**Upload multiplo dà errore**
- Il widget usa `MultiFileInput` con `allow_multiple_selected = True` (Django 5).  
- In view, usa `form.cleaned_data['attachments']` (lista) e non `request.FILES`.

---

## 📜 Licenza
Uso interno.

