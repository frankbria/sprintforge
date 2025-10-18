# SprintForge VPS + Tailscale Deployment - Quick Start

**Your Setup**: VPS + Tailscale (✅ Already configured)
**Deployment Time**: 15-20 minutes
**Access**: Private team access via Tailscale network

---

## 🎯 Your Optimal Path

You have the **ideal setup** for staging:
- ✅ VPS already running (no home server concerns)
- ✅ Tailscale network configured (secure private access)
- ✅ No port forwarding needed
- ✅ No firewall configuration needed
- ✅ Professional and reliable

---

## 🚀 15-Minute Deployment

### Step 1: Prepare VPS (2 minutes)

```bash
# SSH into your VPS
ssh your-vps

# Install Docker (if not already installed)
curl -fsSL https://get.docker.com | sh
sudo usermod -aG docker $USER
newgrp docker

# Verify
docker --version
docker-compose --version

# Install git (if needed)
sudo apt update && sudo apt install -y git
```

### Step 2: Clone Repository (1 minute)

```bash
# Clone to VPS
cd ~
git clone https://github.com/frankbria/sprintforge.git
cd sprintforge
```

### Step 3: Configure Environment (3 minutes)

```bash
# Create staging environment file
cp .env.staging.example .env.staging

# Generate secure keys
echo "SECRET_KEY=$(openssl rand -hex 32)" >> .env.staging
echo "NEXTAUTH_SECRET=$(openssl rand -base64 32)" >> .env.staging
echo "POSTGRES_PASSWORD=$(openssl rand -base64 16)" >> .env.staging

# Edit if needed
nano .env.staging
# Update STAGING_DOMAIN to your VPS Tailscale hostname
```

### Step 4: Deploy Stack (5 minutes)

```bash
# Start all services
docker-compose -f docker-compose.staging.yml --env-file .env.staging up -d

# Wait for services to start (30 seconds)
sleep 30

# Check status
docker-compose -f docker-compose.staging.yml ps

# View logs
docker-compose -f docker-compose.staging.yml logs -f
# Press Ctrl+C to exit logs
```

### Step 5: Health Check (2 minutes)

```bash
# Get your Tailscale IP
tailscale ip -4
# Example output: 100.101.102.103

# Test health endpoint (from VPS)
curl http://localhost:8080/health

# Should return: "healthy"
```

### Step 6: Access from Team Devices (2 minutes)

**From any device on your Tailscale network**:

```
# Get VPS Tailscale IP/hostname
tailscale status | grep your-vps-name

# Access staging environment
Frontend: http://100.101.102.103:8080
Backend API: http://100.101.102.103:8080/api/v1
API Docs: http://100.101.102.103:8080/docs

# Or use Tailscale MagicDNS
Frontend: http://your-vps-name.tail-scale.ts.net:8080
```

---

## 🎪 Sprint Demo Workflow

### Pre-Demo Checklist (5 minutes)

```bash
# SSH into VPS
ssh your-vps
cd ~/sprintforge

# Pull latest code
git pull origin main

# Rebuild and restart
docker-compose -f docker-compose.staging.yml down
docker-compose -f docker-compose.staging.yml build --no-cache
docker-compose -f docker-compose.staging.yml --env-file .env.staging up -d

# Verify health
curl http://localhost:8080/health

# Check all services running
docker-compose -f docker-compose.staging.yml ps
```

### Demo Day Process

**30 Minutes Before Demo**:
1. Deploy latest code (see above)
2. Create demo data if needed
3. Test key user flows
4. Share Tailscale access URL with participants

**During Demo**:
- Share screen showing: `http://your-vps.tail-scale.ts.net:8080`
- Walk through features
- Gather real-time feedback
- Document questions and issues

**After Demo**:
- Update backlog with feedback
- Create tickets for issues
- Document learnings

---

## 📝 Team Access Setup

### For Team Members to Access Staging

**One-Time Setup** (per team member):

1. **Install Tailscale**:
   ```bash
   # macOS
   brew install tailscale

   # Linux
   curl -fsSL https://tailscale.com/install.sh | sh

   # Windows
   # Download from: https://tailscale.com/download/windows
   ```

2. **Connect to Network**:
   ```bash
   tailscale up
   # Follow authentication prompts
   ```

3. **Access Staging**:
   ```
   Open browser: http://your-vps-name.tail-scale.ts.net:8080
   ```

---

## 🔧 Common Operations

### Update Staging with Latest Code

```bash
# SSH to VPS
ssh your-vps
cd ~/sprintforge

# Pull and rebuild
git pull origin main
docker-compose -f docker-compose.staging.yml down
docker-compose -f docker-compose.staging.yml build
docker-compose -f docker-compose.staging.yml --env-file .env.staging up -d

# Verify
curl http://localhost:8080/health
```

### View Logs

```bash
# All services
docker-compose -f docker-compose.staging.yml logs -f

# Specific service
docker-compose -f docker-compose.staging.yml logs -f backend
docker-compose -f docker-compose.staging.yml logs -f frontend

# Last 100 lines
docker-compose -f docker-compose.staging.yml logs --tail=100
```

### Database Backup

```bash
# Manual backup
docker-compose -f docker-compose.staging.yml exec postgres \
  pg_dump -U sprintforge sprintforge_staging > backup-$(date +%Y%m%d).sql

# Restore backup
cat backup-20251017.sql | docker-compose -f docker-compose.staging.yml exec -T postgres \
  psql -U sprintforge sprintforge_staging
```

### Restart Services

```bash
# All services
docker-compose -f docker-compose.staging.yml restart

# Specific service
docker-compose -f docker-compose.staging.yml restart backend
```

### Check Resource Usage

```bash
# Docker stats
docker stats

# Disk usage
df -h
du -sh ~/sprintforge/data

# Memory
free -h
```

---

## 🎯 Advantages of Your Setup

### VPS Benefits
- ✅ Always available (no home internet downtime)
- ✅ Better uptime than home server
- ✅ Professional infrastructure
- ✅ Dedicated resources
- ✅ Easy to upgrade

### Tailscale Benefits
- ✅ Zero port forwarding (secure by default)
- ✅ No firewall configuration
- ✅ Encrypted traffic
- ✅ Works from anywhere
- ✅ Mobile access (iOS/Android apps)
- ✅ Access control built-in

### Combined Benefits
- ✅ Production-like environment
- ✅ Team can access from anywhere
- ✅ Secure (not publicly exposed)
- ✅ Simple setup
- ✅ No SSL certificate hassle
- ✅ Perfect for demos

---

## 🔒 Security Notes

### Already Secure
- ✅ No public internet exposure
- ✅ Tailscale encryption (WireGuard)
- ✅ Access control via Tailscale ACLs
- ✅ VPS firewall (if configured)

### Optional Enhancements

**Tailscale ACLs** (restrict access to specific team members):
```json
// In Tailscale admin console
{
  "acls": [
    {
      "action": "accept",
      "users": ["user1@example.com", "user2@example.com"],
      "ports": ["your-vps:8080"]
    }
  ]
}
```

**VPS Firewall** (optional, Tailscale already provides protection):
```bash
# Only allow SSH and Tailscale
sudo ufw default deny incoming
sudo ufw default allow outgoing
sudo ufw allow 22/tcp
sudo ufw allow 41641/udp  # Tailscale
sudo ufw enable
```

---

## 🐛 Troubleshooting

### Can't Access from Team Device

**Check 1**: Verify Tailscale connected
```bash
tailscale status
# Should show "Connected"
```

**Check 2**: Ping VPS
```bash
ping your-vps-name.tail-scale.ts.net
```

**Check 3**: Test from VPS itself
```bash
ssh your-vps
curl http://localhost:8080/health
```

### Services Not Starting

```bash
# Check logs
docker-compose -f docker-compose.staging.yml logs

# Check disk space
df -h

# Check memory
free -h

# Restart
docker-compose -f docker-compose.staging.yml restart
```

### Database Connection Errors

```bash
# Check PostgreSQL
docker-compose -f docker-compose.staging.yml logs postgres

# Verify database
docker-compose -f docker-compose.staging.yml exec postgres \
  psql -U sprintforge -d sprintforge_staging -c "SELECT 1;"
```

---

## 📊 Cost Analysis

| Component | Your Cost | Cloud Alternative |
|-----------|-----------|-------------------|
| VPS | Already paid | $5-20/month |
| Tailscale | $0 (free tier) | $0-6/month |
| **Total** | **$0 extra** | **$5-26/month** |

**Your savings**: $60-300/year by using existing infrastructure!

---

## 🎓 Next Steps

### Immediate (Today)
1. ✅ Deploy to VPS (15 minutes)
2. ✅ Test access from team devices
3. ✅ Create demo data
4. ✅ Schedule first demo

### This Week
1. Set up automated deployments (GitHub Actions)
2. Create demo script template
3. Add monitoring (optional)
4. Document common workflows

### Future Enhancements
1. Add public access option (Cloudflare Tunnel on VPS)
2. Set up CI/CD pipeline
3. Add Sentry error tracking
4. Create automated backups

---

## 📞 Quick Reference

**VPS Access**:
```bash
ssh your-vps
cd ~/sprintforge
```

**Start/Stop Stack**:
```bash
# Start
docker-compose -f docker-compose.staging.yml --env-file .env.staging up -d

# Stop
docker-compose -f docker-compose.staging.yml down

# Restart
docker-compose -f docker-compose.staging.yml restart
```

**Access URLs** (via Tailscale):
```
Frontend: http://vps-ip:8080
Backend: http://vps-ip:8080/api/v1
Docs: http://vps-ip:8080/docs
```

**Logs**:
```bash
docker-compose -f docker-compose.staging.yml logs -f
```

---

**Setup Status**: ✅ Ready to deploy in 15 minutes
**Complexity**: ⭐ Very Simple (leverage existing infrastructure)
**Cost**: $0 (using existing resources)
**Security**: ⭐⭐⭐⭐⭐ (Tailscale + private VPS)

---

**Last Updated**: 2025-10-17
**For**: VPS + Tailscale deployment
