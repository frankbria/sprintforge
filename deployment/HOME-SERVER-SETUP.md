# SprintForge Home Server Staging Setup Guide

Complete guide for deploying SprintForge to a home server for sprint demos and internal testing.

---

## 📋 Prerequisites

### Hardware Requirements
- **Minimum**: 2 CPU cores, 4GB RAM, 20GB storage
- **Recommended**: 4 CPU cores, 8GB RAM, 50GB SSD
- **Supported OS**: Linux (Ubuntu 22.04+), macOS, Windows with WSL2

### Software Requirements
```bash
# Required
- Docker (20.10+)
- Docker Compose (2.0+)
- Git

# Optional but recommended
- UFW/firewall
- Fail2ban
- Unattended-upgrades (for Ubuntu)
```

### Network Requirements
- Stable internet connection (10+ Mbps upload recommended)
- No CGNAT restriction (or use Cloudflare Tunnel/Tailscale)

---

## 🚀 Quick Start (30 Minutes)

### Option A: Cloudflare Tunnel (Recommended - Public Access)

**Step 1: Install Docker**
```bash
# Ubuntu/Debian
curl -fsSL https://get.docker.com | sh
sudo usermod -aG docker $USER
newgrp docker

# Verify
docker --version
docker-compose --version
```

**Step 2: Clone and Configure**
```bash
cd ~/projects
git clone https://github.com/frankbria/sprintforge.git
cd sprintforge

# Create staging environment file
cp .env.staging.example .env.staging

# Edit configuration
nano .env.staging
# Update: POSTGRES_PASSWORD, SECRET_KEY, NEXTAUTH_SECRET
```

**Step 3: Set Up Cloudflare Tunnel**
```bash
# 1. Install cloudflared
curl -L https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64.deb -o cloudflared.deb
sudo dpkg -i cloudflared.deb

# 2. Login to Cloudflare (opens browser)
cloudflared tunnel login

# 3. Create tunnel
cloudflared tunnel create sprintforge-staging

# 4. Get tunnel credentials
cat ~/.cloudflared/*.json
# Copy the tunnel token (starts with "eyJ...")

# 5. Add token to .env.staging
echo "CLOUDFLARE_TUNNEL_TOKEN=your_token_here" >> .env.staging

# 6. Configure DNS in Cloudflare Dashboard
# Go to: https://dash.cloudflare.com/
# Zero Trust → Access → Tunnels → sprintforge-staging
# Add Public Hostname:
#   - Subdomain: staging
#   - Domain: yourdomain.com
#   - Service: http://nginx:80
```

**Step 4: Deploy**
```bash
# Build and start all services
docker-compose -f docker-compose.staging.yml --env-file .env.staging up -d

# Check status
docker-compose -f docker-compose.staging.yml ps

# View logs
docker-compose -f docker-compose.staging.yml logs -f

# Test health
curl http://localhost:8080/health
```

**Step 5: Access Your Staging Environment**
```
Frontend: https://staging.yourdomain.com
Backend API: https://staging.yourdomain.com/api/v1
API Docs: https://staging.yourdomain.com/docs
```

---

### Option B: Tailscale (Private Access - Team Only)

**Step 1: Install Tailscale**
```bash
# Install
curl -fsSL https://tailscale.com/install.sh | sh

# Start and authenticate
sudo tailscale up

# Get your Tailscale IP
tailscale ip -4
# Example: 100.101.102.103
```

**Step 2: Deploy Stack**
```bash
# Use same docker-compose.staging.yml but comment out cloudflared service
docker-compose -f docker-compose.staging.yml --env-file .env.staging up -d
```

**Step 3: Access via Tailscale**
```
# Share this with your team (they need Tailscale installed)
http://100.101.102.103:8080

# Or use Tailscale Magic DNS
http://your-hostname.tail-scale.ts.net:8080
```

---

### Option C: ngrok (Quick Demo - Temporary)

**Step 1: Install ngrok**
```bash
# Download and install
curl -s https://ngrok-agent.s3.amazonaws.com/ngrok.asc | \
  sudo tee /etc/apt/trusted.gpg.d/ngrok.asc >/dev/null
echo "deb https://ngrok-agent.s3.amazonaws.com buster main" | \
  sudo tee /etc/apt/sources.list.d/ngrok.list
sudo apt update && sudo apt install ngrok

# Authenticate (get token from https://dashboard.ngrok.com)
ngrok config add-authtoken YOUR_TOKEN
```

**Step 2: Deploy Stack**
```bash
docker-compose -f docker-compose.staging.yml --env-file .env.staging up -d
```

**Step 3: Start Tunnel**
```bash
# Start ngrok tunnel
ngrok http 8080

# You'll get a URL like: https://abc123.ngrok.io
# Share this with demo participants
```

---

## 🔧 Configuration

### Environment Variables

Edit `.env.staging`:

```env
# Required - Change these!
POSTGRES_PASSWORD=your_secure_password_here
SECRET_KEY=generate-random-64-char-string
NEXTAUTH_SECRET=generate-random-64-char-string

# Optional - Cloudflare Tunnel
CLOUDFLARE_TUNNEL_TOKEN=your_tunnel_token_from_cloudflare

# Optional - Custom Domain
STAGING_DOMAIN=staging.yourdomain.com
```

**Generate Secure Keys**:
```bash
# SECRET_KEY
openssl rand -hex 32

# NEXTAUTH_SECRET
openssl rand -base64 32
```

### Custom Domain Setup (Cloudflare)

1. **Add Domain to Cloudflare** (if not already)
   - Go to Cloudflare Dashboard
   - Add Site → Enter your domain
   - Follow DNS migration steps

2. **Create Tunnel**
   ```bash
   cloudflared tunnel create sprintforge-staging
   ```

3. **Configure DNS**
   - Dashboard → Zero Trust → Access → Tunnels
   - Select tunnel → Public Hostname → Add
   - Subdomain: `staging`
   - Domain: `yourdomain.com`
   - Service: `http://nginx:80`

4. **SSL/TLS Settings** (in Cloudflare Dashboard)
   - SSL/TLS → Overview → Full (strict)
   - Edge Certificates → Always Use HTTPS: ON

---

## 🎯 Sprint Demo Workflow

### Weekly Demo Schedule

```
MONDAY (Planning)
├── Review last demo feedback
├── Plan current sprint features
└── Update staging with latest main

WEDNESDAY (Mid-Sprint)
├── Deploy WIP features to staging
├── Internal team review
└── Quick fixes if needed

FRIDAY (Demo Day)
├── Final staging deployment (9 AM)
├── Smoke tests (10 AM)
├── Sprint demo (2 PM)
└── Gather feedback and update backlog
```

### Pre-Demo Checklist

```bash
# 1. Pull latest code
git pull origin main

# 2. Rebuild and deploy
docker-compose -f docker-compose.staging.yml down
docker-compose -f docker-compose.staging.yml build --no-cache
docker-compose -f docker-compose.staging.yml --env-file .env.staging up -d

# 3. Run health checks
curl https://staging.yourdomain.com/health
curl https://staging.yourdomain.com/api/v1/health

# 4. Check logs for errors
docker-compose -f docker-compose.staging.yml logs --tail=50

# 5. Create demo data (if needed)
docker-compose -f docker-compose.staging.yml exec backend python scripts/create_demo_data.py

# 6. Test key user flows
# - Login
# - Create project
# - Run analytics
# - Create baseline
# - Compare baseline
```

### Demo Script Template

```markdown
# Sprint [N] Demo - [Date]

## Agenda (30 min)
1. Sprint recap (5 min)
2. Feature demos (20 min)
3. Q&A and feedback (5 min)

## Features Completed This Sprint

### 1. [Feature Name]
**User Story**: As a [user], I want [goal] so that [benefit]

**Demo Flow**:
1. Navigate to [URL]
2. [Action 1]
3. [Action 2]
4. Show [result]

**Success Criteria**: ✅ [criteria met]

### 2. [Next Feature]
...

## Test Account
- URL: https://staging.yourdomain.com
- Email: demo@sprintforge.com
- Password: Demo123!

## Known Issues
- [Issue 1]: [Workaround if any]

## Feedback Questions
1. Does the workflow feel intuitive?
2. What would you change?
3. Any missing features?
```

---

## 🔍 Monitoring & Maintenance

### Health Checks
```bash
# Check all services
docker-compose -f docker-compose.staging.yml ps

# View logs
docker-compose -f docker-compose.staging.yml logs -f [service_name]

# Restart specific service
docker-compose -f docker-compose.staging.yml restart backend

# Check resource usage
docker stats
```

### Database Backups
```bash
# Manual backup
docker-compose -f docker-compose.staging.yml exec postgres \
  pg_dump -U sprintforge sprintforge_staging > backup-$(date +%Y%m%d).sql

# Automated daily backups (add to cron)
0 2 * * * cd ~/projects/sprintforge && docker-compose -f docker-compose.staging.yml exec -T postgres pg_dump -U sprintforge sprintforge_staging | gzip > ~/backups/staging-$(date +\%Y\%m\%d).sql.gz
```

### Log Management
```bash
# View logs
docker-compose -f docker-compose.staging.yml logs --tail=100 -f

# Save logs to file
docker-compose -f docker-compose.staging.yml logs > staging-logs-$(date +%Y%m%d).txt

# Clear old logs
docker system prune -a --volumes
```

### Updates
```bash
# Pull latest code
git pull origin main

# Rebuild and restart
docker-compose -f docker-compose.staging.yml down
docker-compose -f docker-compose.staging.yml build --no-cache
docker-compose -f docker-compose.staging.yml --env-file .env.staging up -d

# Check health
curl https://staging.yourdomain.com/health
```

---

## 🔒 Security Best Practices

### Firewall Configuration
```bash
# Ubuntu/Debian (UFW)
sudo ufw default deny incoming
sudo ufw default allow outgoing
sudo ufw allow ssh
sudo ufw allow 80/tcp   # If using port forwarding (not recommended)
sudo ufw allow 443/tcp  # If using port forwarding (not recommended)
sudo ufw enable

# Check status
sudo ufw status verbose
```

### Auto-Updates (Ubuntu)
```bash
# Install unattended-upgrades
sudo apt install unattended-upgrades

# Configure
sudo dpkg-reconfigure -plow unattended-upgrades
```

### Fail2Ban (Brute Force Protection)
```bash
# Install
sudo apt install fail2ban

# Configure
sudo cp /etc/fail2ban/jail.conf /etc/fail2ban/jail.local
sudo systemctl enable fail2ban
sudo systemctl start fail2ban
```

### Cloudflare Security Features

If using Cloudflare Tunnel:
- **Zero Trust Access**: Require authentication for staging
- **Rate Limiting**: Prevent abuse
- **WAF Rules**: Block malicious traffic
- **DDoS Protection**: Automatic

---

## 🐛 Troubleshooting

### Service Won't Start
```bash
# Check logs
docker-compose -f docker-compose.staging.yml logs [service_name]

# Check disk space
df -h

# Check memory
free -h

# Restart specific service
docker-compose -f docker-compose.staging.yml restart [service_name]
```

### Database Connection Errors
```bash
# Check PostgreSQL logs
docker-compose -f docker-compose.staging.yml logs postgres

# Test database connection
docker-compose -f docker-compose.staging.yml exec postgres psql -U sprintforge -d sprintforge_staging -c "SELECT 1;"

# Reset database (CAUTION: Deletes all data)
docker-compose -f docker-compose.staging.yml down -v
docker-compose -f docker-compose.staging.yml up -d
```

### Cloudflare Tunnel Not Working
```bash
# Check cloudflared logs
docker-compose -f docker-compose.staging.yml logs cloudflared

# Restart tunnel
docker-compose -f docker-compose.staging.yml restart cloudflared

# Test local nginx
curl http://localhost:8080/health

# Verify tunnel token
echo $CLOUDFLARE_TUNNEL_TOKEN
```

### Out of Disk Space
```bash
# Clean Docker
docker system prune -a --volumes

# Check disk usage
du -sh /var/lib/docker
du -sh ~/projects/sprintforge/data

# Remove old backups
find ~/backups -name "staging-*.sql.gz" -mtime +30 -delete
```

---

## 📊 Cost Comparison

| Method | Setup Time | Monthly Cost | Public Access | Security |
|--------|-----------|--------------|---------------|----------|
| **Cloudflare Tunnel** | 30 min | $0 | ✅ | ⭐⭐⭐⭐⭐ |
| **Tailscale** | 10 min | $0 | Team only | ⭐⭐⭐⭐⭐ |
| **ngrok Free** | 2 min | $0 | ✅ (temp URL) | ⭐⭐⭐ |
| **ngrok Paid** | 5 min | $8/mo | ✅ (custom domain) | ⭐⭐⭐⭐ |
| **DigitalOcean** | 1 hr | $12-25/mo | ✅ | ⭐⭐⭐⭐ |
| **AWS** | 2 hr | $20-40/mo | ✅ | ⭐⭐⭐⭐⭐ |

**Recommendation**: Cloudflare Tunnel for best balance of cost, security, and ease of use.

---

## 🎓 Next Steps

1. **Set Up Monitoring**
   - Add Sentry for error tracking
   - Set up Uptime Robot for availability monitoring

2. **Automate Deployments**
   - GitHub Actions to deploy on push to staging branch
   - Automatic backups to cloud storage

3. **Add Demo Data**
   - Create seed script for sample projects
   - Add demo user accounts

4. **Document Features**
   - Create demo script templates
   - Record demo videos

---

## 📞 Support

**Issues?**
- Check logs: `docker-compose -f docker-compose.staging.yml logs`
- Review troubleshooting section above
- Open GitHub issue with logs

**Resources**:
- [Docker Documentation](https://docs.docker.com/)
- [Cloudflare Tunnel Docs](https://developers.cloudflare.com/cloudflare-one/connections/connect-apps/)
- [Tailscale Docs](https://tailscale.com/kb/)

---

**Last Updated**: 2025-10-17
**Maintainer**: SprintForge Team
