#!/usr/bin/env bash
# ==============================================================================
# StenoVision - AWS Free Tier EC2 Auto-Deployment & Provisioning Script
# Target OS: Ubuntu 22.04 LTS / 24.04 LTS (x86_64)
# Hardware Profile: AWS Free Tier t2.micro or t3.micro (1 vCPU, 1 GB RAM, 30 GB EBS)
# Memory Strategy: Dynamic 3 GB Swapfile Allocation (expands addressable RAM to 4 GB)
# ==============================================================================

set -euo pipefail

echo "=============================================================================="
echo " Starting StenoVision Production Deployment on AWS EC2 Free Tier"
echo " Date: $(date -u +"%Y-%m-%d %H:%M:%SZ")"
echo "=============================================================================="

# 1. Verify Root/Sudo Privileges
if [ "$EUID" -ne 0 ]; then
  echo "[-] Error: Please run this provisioning script with sudo or as root:"
  echo "    sudo bash deploy/aws_ec2_setup.sh"
  exit 1
fi

# Detect calling user
ACTUAL_USER="${SUDO_USER:-$(whoami)}"
ACTUAL_HOME=$(getent passwd "$ACTUAL_USER" | cut -d: -f6)

echo "[+] Running as root for user: ${ACTUAL_USER} (Home: ${ACTUAL_HOME})"

# ------------------------------------------------------------------------------
# 2. Swapfile Provisioning (Critical for 1 GB RAM Free Tier instances)
# ------------------------------------------------------------------------------
echo "------------------------------------------------------------------------------"
echo "[Step 1/6] Configuring 3 GB Linux Swap Space for AWS Free Tier stability..."
echo "------------------------------------------------------------------------------"

if swapon --show | grep -q "/swapfile"; then
  echo "[i] Swapfile already active:"
  swapon --show
else
  echo "[+] Creating 3 GB swapfile at /swapfile..."
  fallocate -l 3G /swapfile || dd if=/dev/zero of=/swapfile bs=1M count=3072 status=progress
  chmod 600 /swapfile
  mkswap /swapfile
  swapon /swapfile

  # Ensure swap persists across EC2 reboots
  if ! grep -q '/swapfile' /etc/fstab; then
    echo '/swapfile none swap sw 0 0' >> /etc/fstab
    echo "[+] Added /swapfile to /etc/fstab for persistence."
  fi

  # Optimize swappiness for low-memory container hosts
  sysctl vm.swappiness=20
  if ! grep -q 'vm.swappiness' /etc/sysctl.conf; then
    echo 'vm.swappiness=20' >> /etc/sysctl.conf
  fi

  echo "[+] Swap configuration complete. Available Memory:"
  free -h
fi

# ------------------------------------------------------------------------------
# 3. System Update & Package Prerequisites
# ------------------------------------------------------------------------------
echo "------------------------------------------------------------------------------"
echo "[Step 2/6] Updating APT repositories and installing core utilities..."
echo "------------------------------------------------------------------------------"

export DEBIAN_FRONTEND=noninteractive
apt-get update -y
apt-get install -y --no-install-recommends \
  apt-transport-https \
  ca-certificates \
  curl \
  gnupg \
  lsb-release \
  git \
  ufw \
  htop \
  jq

# ------------------------------------------------------------------------------
# 4. Install Official Docker Engine & Docker Compose Plugin
# ------------------------------------------------------------------------------
echo "------------------------------------------------------------------------------"
echo "[Step 3/6] Installing Docker Engine and Docker Compose V2..."
echo "------------------------------------------------------------------------------"

if command -v docker &> /dev/null; then
  echo "[i] Docker already installed: $(docker --version)"
else
  install -m 0755 -d /etc/apt/keyrings
  curl -fsSL https://download.docker.com/linux/ubuntu/gpg | gpg --dearmor --yes -o /etc/apt/keyrings/docker.gpg
  chmod a+r /etc/apt/keyrings/docker.gpg

  UBUNTU_CODENAME=$(lsb_release -cs)
  echo \
    "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu \
    ${UBUNTU_CODENAME} stable" | tee /etc/apt/sources.list.d/docker.list > /dev/null

  apt-get update -y
  apt-get install -y --no-install-recommends \
    docker-ce \
    docker-ce-cli \
    containerd.io \
    docker-buildx-plugin \
    docker-compose-plugin

  systemctl enable docker
  systemctl start docker
  echo "[+] Docker Engine installed successfully."
fi

# Add invoking user to docker group
if ! groups "$ACTUAL_USER" | grep -q "\bdocker\b"; then
  usermod -aG docker "$ACTUAL_USER"
  echo "[+] Added user ${ACTUAL_USER} to docker group."
fi

# ------------------------------------------------------------------------------
# 5. Firewall Configuration (UFW)
# ------------------------------------------------------------------------------
echo "------------------------------------------------------------------------------"
echo "[Step 4/6] Configuring Security Firewall (UFW)..."
echo "------------------------------------------------------------------------------"

ufw allow 22/tcp comment 'SSH Remote Access' || true
ufw allow 80/tcp comment 'Nginx HTTP Gateway' || true
ufw allow 443/tcp comment 'HTTPS Secure Gateway' || true
ufw allow 3001/tcp comment 'Grafana Clinical Dashboards' || true
ufw allow 9090/tcp comment 'Prometheus Metrics UI' || true
echo "y" | ufw enable || true
echo "[+] Firewall rules applied."

# ------------------------------------------------------------------------------
# 6. Verify Workspace & Build Containers
# ------------------------------------------------------------------------------
echo "------------------------------------------------------------------------------"
echo "[Step 5/6] Validating StenoVision Project Directory & Launching Stack..."
echo "------------------------------------------------------------------------------"

# Locate docker-compose.yml
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"

cd "${PROJECT_ROOT}"

if [ ! -f "docker-compose.yml" ]; then
  echo "[-] Error: docker-compose.yml not found in ${PROJECT_ROOT}"
  exit 1
fi

# Prepare persistent logs and static directories with correct permissions
mkdir -p backend/logs backend/static/reports backend/static/uploads backend/static/xai
chmod -R 777 backend/logs backend/static

echo "[+] Building and launching StenoVision multi-container stack via Docker Compose..."
docker compose build --parallel
docker compose up -d

# ------------------------------------------------------------------------------
# 7. Deployment Health Verification
# ------------------------------------------------------------------------------
echo "------------------------------------------------------------------------------"
echo "[Step 6/6] Verifying Services & Healthchecks..."
echo "------------------------------------------------------------------------------"

echo "[i] Waiting 15 seconds for containers to initialize..."
sleep 15

docker compose ps

# Fetch Public IP
PUBLIC_IP=$(curl -s -m 5 https://checkip.amazonaws.com || curl -s -m 5 https://ifconfig.me || echo "<EC2_PUBLIC_IP>")

echo ""
echo "=============================================================================="
echo " StenoVision Platform Successfully Deployed!"
echo "=============================================================================="
echo " Access Endpoints:"
echo "   - Unified Web Portal:       http://${PUBLIC_IP} (Nginx Gateway)"
echo "   - Clinical Workstation UI:  http://${PUBLIC_IP}:3000 (Next.js Direct)"
echo "   - REST API & Swagger Docs:  http://${PUBLIC_IP}/docs"
echo "   - System Healthcheck:       http://${PUBLIC_IP}/health"
echo "   - Prometheus Live Metrics:  http://${PUBLIC_IP}:9090"
echo "   - Grafana AI Dashboards:    http://${PUBLIC_IP}:3001"
echo "       Credentials:  Username: admin"
echo "                     Password: stenovision_admin"
echo ""
echo " Real-Time Observability Commands:"
echo "   - View Live API Logs:       docker logs -f stenovision_backend"
echo "   - View HIPAA Scrubbed Logs: cat backend/logs/stenovision.log"
echo "   - View Stack Resource Usage: docker stats"
echo "=============================================================================="
