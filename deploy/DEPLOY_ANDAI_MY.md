# Serve ANDAI on **andai.my** with nginx

This guide assumes a **Linux server** (Ubuntu 22.04/24.04 or Debian) with a **public IPv4** address. Your Mac can be the dev machine; production usually runs on a **VPS** (DigitalOcean, AWS Lightsail, Vultr, etc.) or a dedicated server.

Traffic flow:

```text
Internet → DNS (andai.my) → your server :443 → nginx → Next.js :3000 → (rewrites) FastAPI :8000
```

You only need nginx to proxy **port 3000**. The Next.js app already forwards `/api/*` to the Python API on `127.0.0.1:8000`.

---

## 1. Point **andai.my** to your server (DNS)

At your **domain registrar** (where you bought `andai.my` — e.g. MYNIC, Cloudflare, Namecheap):

1. Open **DNS management** for `andai.my`.
2. Add an **A record**:
   - **Host / Name:** `@` (or blank, or `andai.my` — depends on the panel; means the root domain).
   - **Value / Points to:** your server’s **public IPv4** (e.g. `203.0.113.50`).
   - **TTL:** 300 or Auto.

3. Optional **www**:
   - **A record:** `www` → same IPv4, **or**
   - **CNAME:** `www` → `andai.my.`

4. Wait for propagation (often **5–30 minutes**, sometimes up to 48 hours). Check:

   ```bash
   dig +short andai.my A
   ```

   It should return your server IP.

**If you use Cloudflare “orange cloud” proxy:** you can still use Let’s Encrypt (certbot in **DNS** or **webroot** mode). For the simplest path, use **DNS only** (grey cloud) until TLS works, or use Cloudflare’s own origin certificate and set nginx to Full (strict).

---

## 2. Server preparation

SSH into the server as root or with `sudo`.

```bash
sudo apt update && sudo apt install -y nginx certbot python3-certbot-nginx
```

Open the firewall (if `ufw` is enabled):

```bash
sudo ufw allow OpenSSH
sudo ufw allow 'Nginx Full'   # or: allow 80,443/tcp
sudo ufw enable
```

---

## 3. Run the app (production-style)

On the server, clone or copy `local_llm`, install **PostgreSQL**, **Redis**, **Ollama** (if LLM runs on this machine), **Node 22+**, **Python 3.12+**, then:

**Backend** (`backend/.env`):

- Set `FRONTEND_URL=https://andai.my` and, if you serve **www** as well, add  
  `CORS_EXTRA_ORIGINS=https://www.andai.my` in `backend/.env` (comma-separated list allowed).
- Use strong `SECRET_KEY` and production DB credentials.

```bash
cd /path/to/local_llm/backend
python3.12 -m venv venv
./venv/bin/pip install -r requirements.txt
./venv/bin/alembic upgrade head
./venv/bin/python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

Use **systemd** or **tmux** so this keeps running; see §6.

**Frontend:**

```bash
cd /path/to/local_llm/frontend
pnpm install
pnpm build
pnpm start -- --hostname 127.0.0.1 --port 3000
```

`pnpm start` binds to localhost only so only nginx (on the same machine) can reach it.

---

## 4. nginx config

Copy the site config from this repo:

```bash
sudo cp /path/to/local_llm/deploy/nginx/andai.my.conf /etc/nginx/sites-available/andai.my
sudo ln -sf /etc/nginx/sites-available/andai.my /etc/nginx/sites-enabled/
sudo rm -f /etc/nginx/sites-enabled/default   # optional, if it conflicts
sudo nginx -t && sudo systemctl reload nginx
```

Confirm **DNS already resolves** to this server before HTTPS.

---

## 5. HTTPS with Let’s Encrypt

```bash
sudo certbot --nginx -d andai.my -d www.andai.my
```

Follow prompts (email, agree to terms). Certbot will adjust nginx for SSL and renewals.

Auto-renewal is usually installed as a timer; test with:

```bash
sudo certbot renew --dry-run
```

---

## 6. Keep processes running (systemd examples)

**API** — `/etc/systemd/system/andai-api.service`:

```ini
[Unit]
Description=ANDAI FastAPI
After=network.target postgresql.service redis.service

[Service]
User=www-data
Group=www-data
WorkingDirectory=/path/to/local_llm/backend
Environment=PATH=/path/to/local_llm/backend/venv/bin
ExecStart=/path/to/local_llm/backend/venv/bin/python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
Restart=always

[Install]
WantedBy=multi-user.target
```

**Web** — `/etc/systemd/system/andai-web.service`:

```ini
[Unit]
Description=ANDAI Next.js
After=network.target andai-api.service

[Service]
User=www-data
Group=www-data
WorkingDirectory=/path/to/local_llm/frontend
Environment=NODE_ENV=production
ExecStart=/usr/bin/pnpm exec next start --hostname 127.0.0.1 --port 3000
Restart=always

[Install]
WantedBy=multi-user.target
```

Adjust `User`, paths, and use full path to `pnpm` (`which pnpm`) if needed. Then:

```bash
sudo systemctl daemon-reload
sudo systemctl enable --now andai-api andai-web
```

---

## 7. CORS

FastAPI uses `FRONTEND_URL` from `.env`. Set:

```env
FRONTEND_URL=https://andai.my
CORS_EXTRA_ORIGINS=https://www.andai.my
```

If you only use the apex domain, omit `CORS_EXTRA_ORIGINS` and redirect `www` → apex in nginx (recommended).

---

## 8. Serving from home instead of a VPS

You would:

1. Forward **80** and **443** on your router to your PC’s LAN IP.
2. Use a **static IP** or DDNS if your home IP changes.
3. Install nginx the same way on that machine (Linux) or use **Docker** / **OrbStack** on Mac with published ports — still need port forwarding and DNS **A** record to the home public IP.

Home hosting is more fragile (CGNAT, dynamic IP, security). A small VPS is usually easier for a public domain.

---

## 9. Quick checklist

| Step | Action |
|------|--------|
| DNS | `A` `@` → server public IP; optional `www` |
| Server | nginx + app on `127.0.0.1:3000` and `:8000` |
| Env | `FRONTEND_URL=https://andai.my`, strong secrets |
| TLS | `certbot --nginx -d andai.my -d www.andai.my` |
| Firewall | Allow 80, 443 (and 22 for SSH) |

---

## Files in this repo

- `deploy/nginx/andai.my.conf` — HTTP reverse proxy (certbot extends to HTTPS).
- `deploy/nginx/andai.my-ssl-snippet.conf` — reference for what certbot typically produces.

If anything fails, check:

```bash
sudo nginx -t
sudo journalctl -u nginx -n 50 --no-pager
curl -I http://127.0.0.1:3000
curl -I http://127.0.0.1:8000/health
```
