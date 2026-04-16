#!/bin/bash
# Shared config for all Rabbit GCP scripts.
# Change values here, every script inherits them.

# ------------------------------------------------------------
# GCP project / location
# ------------------------------------------------------------
export PROJECT_ID="rabbit-492510"
export REGION="asia-south1"
export ZONE="asia-south1-b"

# ------------------------------------------------------------
# Instance sizing (L4 Spot — cheap, fits Qwen 32B 4-bit)
# ------------------------------------------------------------
export MACHINE_TYPE="g2-standard-8"              # 1× L4, 8 vCPU, 32 GB RAM
export ACCELERATOR="type=nvidia-l4,count=1"

# Disk: 150 GB is enough for 4-bit Qwen (~20 GB) + Rabbit LoRA (~1.1 GB) + headroom
export DISK_SIZE="150GB"
export DISK_TYPE="pd-balanced"

# ------------------------------------------------------------
# Base image (Deep Learning VM — PyTorch + CUDA + NVIDIA drivers pre-installed)
# Using pytorch-2-9-cu129 (torch 2.9, CUDA 12.9, NVIDIA 580) — matches Unsloth's
# expected stack from training so bake is faster and more reliable.
# ------------------------------------------------------------
export BASE_IMAGE_FAMILY="pytorch-2-9-cu129-ubuntu-2204-nvidia-580"
export BASE_IMAGE_PROJECT="deeplearning-platform-release"

# ------------------------------------------------------------
# Baked image (what 00_bake_disk.sh produces, what vm_spawn.sh consumes)
# ------------------------------------------------------------
export IMAGE_FAMILY="rabbit-v2"                  # family → always picks latest
export IMAGE_NAME_PREFIX="rabbit-v2"             # individual images get a timestamp suffix

# ------------------------------------------------------------
# VM + networking
# ------------------------------------------------------------
export VM_NAME="rabbit-v2"
export STATIC_IP_NAME="rabbit-static"
export FIREWALL_RULE="rabbit-allow-8000"
export NETWORK_TAG="rabbit-server"
export RABBIT_PORT="8000"
