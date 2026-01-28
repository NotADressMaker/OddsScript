# Deployment Guide

Complete guide for deploying SportsBetLang API to production on popular platforms.

## Quick Deploy Options

| Platform | Difficulty | Cost | Best For |
|----------|-----------|------|----------|
| [Railway](#railway) | ⭐ Easy | Free tier | Quick demo deploys |
| [Replit](#replit) | ⭐ Easy | Free tier | Testing & prototypes |
| [Heroku](#heroku) | ⭐⭐ Easy | $5-7/mo | Small to medium apps |
| [DigitalOcean](#digitalocean-app-platform) | ⭐⭐ Medium | $5/mo | Full control |
| [AWS Elastic Beanstalk](#aws-elastic-beanstalk) | ⭐⭐⭐ Medium | Variable | Enterprise scale |
| [Google Cloud Run](#google-cloud-run) | ⭐⭐ Easy | Pay per use | Serverless |
| [Fly.io](#flyio) | ⭐⭐ Easy | Free tier | Edge computing |
| [VPS (Ubuntu)](#vps-ubuntu-server) | ⭐⭐⭐ Hard | $5-10/mo | Maximum control |

---

## Railway

**Best for:** Quick deployments, demos, prototypes
**Cost:** Free tier available, then usage-based
**Deploy time:** ~5 minutes

### Steps:

1. **Push code to GitHub**
   ```bash
   git add .
   git commit -m "Prepare for deployment"
   git push origin main
   ```

2. **Go to [railway.app](https://railway.app/)**
   - Sign up/login with GitHub
   - Click "New Project"
   - Select "Deploy from GitHub repo"
   - Choose your SportsBetLang repository

3. **Configure environment**
   - Railway auto-detects Python
   - Add environment variable: `PORT=8000`
   - Database will persist in volume

4. **Update start command** (Railway Settings)
   ```
   uvicorn api:app --host 0.0.0.0 --port $PORT
   ```

5. **Deploy!**
   - Railway automatically builds and deploys
   - Get your URL: `https://your-app.railway.app`

**Custom Domain:**
- Go to Settings → Domains
- Add custom domain and configure DNS

---

## Replit

**Best for:** Quick testing, sharing with others
**Cost:** Free tier, $7/mo for Always-On
**Deploy time:** ~2 minutes

### Steps:

1. **Go to [replit.com](https://replit.com/)**
   - Create new Python Repl
   - Import from GitHub (paste your repo URL)

2. **Add `.replit` config** (already included)
   ```toml
   run = "uvicorn api:app --host 0.0.0.0 --port 8000"
   language = "python3"
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements-api.txt
   ```

4. **Run**
   - Click the Run button
   - Get public URL from Replit

5. **Keep it running** (optional)
   - Upgrade to Hacker plan ($7/mo)
   - Enable "Always On"

**Note:** Free tier goes to sleep after inactivity.

---

## Heroku

**Best for:** Production apps, automatic scaling
**Cost:** $5-7/month (Eco dynos)
**Deploy time:** ~10 minutes

### Steps:

1. **Install Heroku CLI**
   ```bash
   # macOS
   brew tap heroku/brew && brew install heroku

   # Ubuntu/Debian
   curl https://cli-assets.heroku.com/install.sh | sh

   # Windows
   # Download from heroku.com/downloads
   ```

2. **Login and create app**
   ```bash
   heroku login
   heroku create sportsbetlang-api
   ```

3. **Add Procfile** to your repo
   ```
   web: uvicorn api:app --host 0.0.0.0 --port $PORT
   ```

4. **Configure buildpack**
   ```bash
   heroku buildpacks:set heroku/python
   ```

5. **Deploy**
   ```bash
   git push heroku main
   ```

6. **View logs**
   ```bash
   heroku logs --tail
   ```

7. **Open app**
   ```bash
   heroku open
   ```

**Database Persistence:**
```bash
# Add persistent storage (if needed for large database)
heroku addons:create heroku-postgresql:mini
```

**Custom Domain:**
```bash
heroku domains:add www.yourdomain.com
# Then configure DNS CNAME to point to Heroku
```

**Environment Variables:**
```bash
heroku config:set VARIABLE_NAME=value
```

---

## DigitalOcean App Platform

**Best for:** Production apps with databases
**Cost:** $5/month minimum
**Deploy time:** ~15 minutes

### Steps:

1. **Go to [DigitalOcean](https://www.digitalocean.com/)**
   - Sign up/login
   - Go to Apps → Create App

2. **Connect GitHub**
   - Authorize DigitalOcean
   - Select your SportsBetLang repository
   - Choose branch (main)

3. **Configure app**
   - **Type:** Web Service
   - **Environment:** Python
   - **Build Command:**
     ```bash
     pip install -r requirements-api.txt
     ```
   - **Run Command:**
     ```bash
     uvicorn api:app --host 0.0.0.0 --port 8080
     ```

4. **Environment Variables**
   - Add any required variables
   - PORT is automatically set to 8080

5. **Choose plan**
   - Basic ($5/mo) for small apps
   - Professional ($12/mo) for production

6. **Deploy!**
   - Click "Create Resources"
   - Wait 5-10 minutes for build
   - Get URL: `https://your-app.ondigitalocean.app`

**Custom Domain:**
- Go to Settings → Domains
- Add domain and configure DNS

**Database:**
- Add DigitalOcean Managed PostgreSQL if needed
- Connection string available as env variable

---

## AWS Elastic Beanstalk

**Best for:** Enterprise applications, AWS ecosystem
**Cost:** EC2 instance costs (~$10-50/mo)
**Deploy time:** ~20 minutes

### Steps:

1. **Install AWS CLI and EB CLI**
   ```bash
   pip install awscli awsebcli
   aws configure
   ```

2. **Initialize Elastic Beanstalk**
   ```bash
   eb init -p python-3.11 sportsbetlang-api
   ```

3. **Create application config** (`.ebextensions/python.config`)
   ```yaml
   option_settings:
     aws:elasticbeanstalk:container:python:
       WSGIPath: api:app
     aws:elasticbeanstalk:application:environment:
       PORT: "8000"
   ```

4. **Create Procfile**
   ```
   web: uvicorn api:app --host 0.0.0.0 --port 8000
   ```

5. **Create and deploy**
   ```bash
   eb create sportsbetlang-prod
   eb deploy
   ```

6. **View status**
   ```bash
   eb status
   eb open
   ```

**Environment Variables:**
```bash
eb setenv VARIABLE_NAME=value
```

**Auto Scaling:**
```bash
eb scale 2  # Run 2 instances
```

**Custom Domain:**
- Use Route 53 or your DNS provider
- Point to EB environment URL

---

## Google Cloud Run

**Best for:** Serverless, pay-per-use
**Cost:** Free tier, then pay per request
**Deploy time:** ~15 minutes

### Steps:

1. **Install gcloud CLI**
   ```bash
   # Follow instructions at cloud.google.com/sdk/install
   gcloud init
   ```

2. **Create Dockerfile** (already included)

3. **Build and push to Container Registry**
   ```bash
   gcloud builds submit --tag gcr.io/YOUR_PROJECT_ID/sportsbetlang-api
   ```

4. **Deploy to Cloud Run**
   ```bash
   gcloud run deploy sportsbetlang-api \
     --image gcr.io/YOUR_PROJECT_ID/sportsbetlang-api \
     --platform managed \
     --region us-central1 \
     --allow-unauthenticated \
     --port 8000
   ```

5. **Get URL**
   ```bash
   gcloud run services describe sportsbetlang-api --format 'value(status.url)'
   ```

**Environment Variables:**
```bash
gcloud run services update sportsbetlang-api \
  --set-env-vars VARIABLE_NAME=value
```

**Custom Domain:**
```bash
gcloud run domain-mappings create \
  --service sportsbetlang-api \
  --domain www.yourdomain.com
```

---

## Fly.io

**Best for:** Edge computing, global deployment
**Cost:** Free tier available
**Deploy time:** ~10 minutes

### Steps:

1. **Install flyctl**
   ```bash
   # macOS/Linux
   curl -L https://fly.io/install.sh | sh

   # Windows
   # Download from fly.io/docs/getting-started/installing-flyctl/
   ```

2. **Login**
   ```bash
   flyctl auth login
   ```

3. **Initialize app**
   ```bash
   flyctl launch
   ```

4. **Configure** (`fly.toml` is created automatically)
   ```toml
   app = "sportsbetlang-api"

   [env]
     PORT = "8000"

   [[services]]
     internal_port = 8000
     protocol = "tcp"

     [[services.ports]]
       handlers = ["http"]
       port = 80

     [[services.ports]]
       handlers = ["tls", "http"]
       port = 443
   ```

5. **Deploy**
   ```bash
   flyctl deploy
   ```

6. **Open app**
   ```bash
   flyctl open
   ```

**Environment Variables:**
```bash
flyctl secrets set VARIABLE_NAME=value
```

**Scale:**
```bash
flyctl scale count 2  # Run 2 instances
```

---

## VPS (Ubuntu Server)

**Best for:** Maximum control, custom configuration
**Cost:** $5-10/month (DigitalOcean, Linode, Vultr)
**Deploy time:** ~30 minutes

### Steps:

1. **Create VPS**
   - Choose Ubuntu 22.04 LTS
   - At least 1GB RAM
   - SSH key authentication

2. **SSH into server**
   ```bash
   ssh root@your-server-ip
   ```

3. **Update system**
   ```bash
   apt update && apt upgrade -y
   ```

4. **Install Python and dependencies**
   ```bash
   apt install python3.11 python3-pip git nginx -y
   ```

5. **Clone repository**
   ```bash
   cd /opt
   git clone https://github.com/YOUR_USERNAME/SportsBetLang.git
   cd SportsBetLang
   ```

6. **Install Python dependencies**
   ```bash
   pip3 install -r requirements-api.txt
   ```

7. **Create systemd service** (`/etc/systemd/system/sportsbetlang.service`)
   ```ini
   [Unit]
   Description=SportsBetLang API
   After=network.target

   [Service]
   User=www-data
   WorkingDirectory=/opt/SportsBetLang
   ExecStart=/usr/local/bin/uvicorn api:app --host 0.0.0.0 --port 8000
   Restart=always

   [Install]
   WantedBy=multi-user.target
   ```

8. **Start service**
   ```bash
   systemctl daemon-reload
   systemctl start sportsbetlang
   systemctl enable sportsbetlang
   systemctl status sportsbetlang
   ```

9. **Configure Nginx** (`/etc/nginx/sites-available/sportsbetlang`)
   ```nginx
   server {
       listen 80;
       server_name your-domain.com;

       location / {
           proxy_pass http://localhost:8000;
           proxy_set_header Host $host;
           proxy_set_header X-Real-IP $remote_addr;
           proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
           proxy_set_header X-Forwarded-Proto $scheme;
       }
   }
   ```

10. **Enable site**
    ```bash
    ln -s /etc/nginx/sites-available/sportsbetlang /etc/nginx/sites-enabled/
    nginx -t
    systemctl restart nginx
    ```

11. **Setup SSL with Let's Encrypt**
    ```bash
    apt install certbot python3-certbot-nginx -y
    certbot --nginx -d your-domain.com
    ```

12. **Configure firewall**
    ```bash
    ufw allow 80
    ufw allow 443
    ufw allow 22
    ufw enable
    ```

---

## Environment Variables

For all platforms, set these environment variables as needed:

```bash
# Database
DATABASE_PATH=/path/to/betting.db

# API Configuration
API_HOST=0.0.0.0
API_PORT=8000

# CORS (production)
CORS_ORIGINS=https://yourdomain.com,https://app.yourdomain.com

# Optional: Authentication
API_KEY=your-secret-key
```

---

## SSL/HTTPS

### Automatic SSL (Recommended)
- **Railway, Heroku, DigitalOcean, Cloud Run, Fly.io:** SSL is automatic
- **Replit:** Automatic HTTPS for all apps

### Manual SSL (VPS)
Use Let's Encrypt (free):
```bash
certbot --nginx -d yourdomain.com
```

---

## Monitoring & Logs

### Railway
```bash
railway logs
```

### Heroku
```bash
heroku logs --tail
```

### DigitalOcean
- View logs in dashboard under Runtime Logs
- Or use CLI: `doctl apps logs <app-id>`

### AWS
```bash
eb logs
```

### Google Cloud Run
```bash
gcloud logging read "resource.type=cloud_run_revision"
```

### VPS
```bash
journalctl -u sportsbetlang -f
```

---

## Performance Optimization

### 1. Use Gunicorn for production (instead of uvicorn alone)

**Update start command:**
```bash
gunicorn api:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
```

### 2. Enable Caching

Add Redis for caching predictions:
```python
# In api.py
import redis
cache = redis.Redis(host='localhost', port=6379, db=0)
```

### 3. Database Optimization

For high traffic, use PostgreSQL instead of SQLite:
```bash
# Install psycopg2
pip install psycopg2-binary
```

### 4. CDN for Static Files

Use Cloudflare or AWS CloudFront for frontend assets.

### 5. Rate Limiting

Add rate limiting to prevent abuse:
```python
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
```

---

## Scaling

### Horizontal Scaling
- **Railway:** Auto-scales based on demand
- **Heroku:** `heroku ps:scale web=3`
- **AWS:** Configure auto-scaling group
- **DigitalOcean:** Increase instance count in dashboard

### Database Scaling
- SQLite: Good for up to ~100k requests/day
- PostgreSQL: For higher traffic
- MongoDB: For document-based data

---

## Cost Estimates

| Platform | Free Tier | Small App | Medium App | Large App |
|----------|-----------|-----------|------------|-----------|
| Railway | $5/mo | $5-10 | $20-40 | $100+ |
| Replit | Free (with sleep) | $7 | $7 | $20 |
| Heroku | None | $7 | $25 | $250+ |
| DigitalOcean | None | $5 | $12 | $50+ |
| AWS | 12mo free | $10-20 | $50-100 | $500+ |
| Google Cloud | Free tier | $5-10 | $30-50 | $200+ |
| Fly.io | Yes | $0-5 | $10-20 | $100+ |
| VPS | None | $5 | $10 | $40+ |

---

## Troubleshooting

### Port Issues
- Most platforms set `$PORT` environment variable
- Update command: `uvicorn api:app --host 0.0.0.0 --port $PORT`

### Database Not Persisting
- Ensure database path is in a persistent volume
- Check platform docs for volume mounting

### CORS Errors
- Update `allow_origins` in `api.py` to your frontend URL
- Don't use `"*"` in production

### Memory Issues
- Increase instance size
- Optimize database queries
- Use caching

### Slow Response Times
- Use Gunicorn with multiple workers
- Add database indexes
- Enable caching
- Use CDN for static files

---

## Security Checklist

- [ ] Enable HTTPS (SSL certificate)
- [ ] Set secure CORS origins (not `*`)
- [ ] Add API authentication
- [ ] Implement rate limiting
- [ ] Use environment variables for secrets
- [ ] Enable firewall rules
- [ ] Keep dependencies updated
- [ ] Monitor logs for suspicious activity
- [ ] Use strong database passwords
- [ ] Backup database regularly

---

## Recommended Setup

**For Quick Testing:**
→ Railway or Replit (5 minutes)

**For Small Projects:**
→ Fly.io or DigitalOcean App Platform ($5-12/mo)

**For Production:**
→ AWS Elastic Beanstalk or Google Cloud Run (scalable)

**For Full Control:**
→ VPS with Ubuntu, Nginx, Let's Encrypt ($5-10/mo)

---

## Next Steps

1. Choose a platform based on your needs
2. Follow the deployment steps above
3. Test your API at the provided URL
4. Configure custom domain (optional)
5. Set up monitoring and backups
6. Enable authentication if needed
7. Add to your frontend/mobile app

---

For questions or issues, see the [Full-Stack Guide](FULLSTACK_GUIDE.md) or open an issue on GitHub.
