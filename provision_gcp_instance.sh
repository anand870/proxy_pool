#!/usr/bin/env bash

# Exit immediately if a command exits with a non-zero status
set -e

# ==============================================================================
# Configuration Variables
# Note: Google Cloud uses 'e2-micro' as its micro instance type (equivalent to AWS ec2 micro).
# ==============================================================================
INSTANCE_NAME="${INSTANCE_NAME:-my-gcp-micro-instance}"
ZONE="${ZONE:-us-central1-a}"
MACHINE_TYPE="${MACHINE_TYPE:-e2-micro}"
IMAGE_FAMILY="${IMAGE_FAMILY:-ubuntu-2204-lts}"
IMAGE_PROJECT="${IMAGE_PROJECT:-ubuntu-os-cloud}"

echo "============================================================"
echo " Provisioning Google Cloud Instance"
echo " Instance Name: ${INSTANCE_NAME}"
echo " Machine Type : ${MACHINE_TYPE}"
echo " Zone         : ${ZONE}"
echo " Image        : ${IMAGE_FAMILY} (${IMAGE_PROJECT})"
echo "============================================================"

# Define startup script to update apt and install git upon VM boot
STARTUP_SCRIPT=$(cat << 'EOF'
#!/bin/bash
export DEBIAN_FRONTEND=noninteractive
apt-get update -y
apt-get install -y git
echo "Git installation completed at $(date)" >> /var/log/startup-script-git.log
git --version >> /var/log/startup-script-git.log
EOF
)

# Provision the Compute Engine VM instance
gcloud compute instances create "${INSTANCE_NAME}" \
    --zone="${ZONE}" \
    --machine-type="${MACHINE_TYPE}" \
    --image-family="${IMAGE_FAMILY}" \
    --image-project="${IMAGE_PROJECT}" \
    --metadata=startup-script="${STARTUP_SCRIPT}" \
    --scopes=cloud-platform

echo ""
echo " Successfully created instance '${INSTANCE_NAME}'."
echo " Git is being installed automatically via the startup script."
echo ""
echo "To SSH into your instance:"
echo "  gcloud compute ssh ${INSTANCE_NAME} --zone=${ZONE}"
echo ""
echo "To check git version inside the VM:"
echo "  gcloud compute ssh ${INSTANCE_NAME} --zone=${ZONE} --command='git --version'"
