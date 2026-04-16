# Rabbit v2.0 Serving — Scrappy GCP Deployment

Two-person testing stack. L4 Spot VM in us-central1-a. Cheap. Verbose logs.

## Stack

- **GCP** project `rabbit-492510`, zone `us-central1-a`
- **Machine**: `g2-standard-8` (1× NVIDIA L4 24GB, 8 vCPU, 32 GB RAM)
- **Mode**: Spot (~$0.22/hr)
- **Baked image**: Qwen 32B (4-bit) + Rabbit v2.0 LoRA pre-downloaded
- **Cold start**: ~60-90 sec from `rabbit wake` to `/health: 200`
- **Auto-stop**: after 20 min idle
- **Inference**: Unsloth + streaming, ~15-25 tok/s on L4
- **Auth**: shared bearer token, one per VM bake

## Budget

| Item | Cost |
|---|---|
| Static IP (always) | ~$3/mo |
| Boot disk 150 GB (always) | ~$15/mo |
| Compute (6 hrs/day Spot L4) | ~$40/mo |
| **Total realistic** | **~$58/mo** |
| **$300 credit runway** | **~5 months** |

## First-time setup

```bash
# 1. Set HF_TOKEN (needed to download private reattend/rabbit-v2.0)
export HF_TOKEN=<your-huggingface-token>

# 2. Add the CLI to PATH (one-time, add to .zshrc for persistence)
export PATH="$HOME/Desktop/rabbit/cli:$PATH"

# 3. Bake the image (one-time, ~20 min, ~$1-2)
cd ~/Desktop/rabbit/serving/gcp
bash 00_bake_disk.sh
```

The bake prints a random `RABBIT_TOKEN` and saves it to `~/.rabbit_token`. Share that token with your friend.

## Daily use

```bash
rabbit wake                                    # ~90s cold start
rabbit extract "Tom said we'd ship by May 15"
rabbit triage --file meeting_notes.txt
rabbit logs                                    # tail server logs
rabbit stop                                    # or let auto-stop fire
```

## Sharing with your friend

1. Give them Compute Instance Admin IAM on the project
2. Give them `~/.rabbit_token` contents
3. Give them this repo (the `serving/` + `cli/` folders)
4. They run `rabbit wake` / `rabbit extract …` exactly like you do

Only one of you tests at a time (as agreed). Auto-stop handles idle gaps.

## Debugging

```bash
rabbit health            # GET /health
rabbit logs              # tail the server log via SSH
rabbit ssh               # raw SSH into the VM
rabbit status            # VM state + last request time

# Inside the VM:
sudo journalctl -u rabbit -n 200        # systemd logs
tail -f /var/log/rabbit/server.log      # structured JSON logs
```

Every request emits JSON: `request_id`, `signal`, `prompt_hash`, `prompt_preview`,
`input_tokens`, `output_tokens`, `latency_ms`, `tokens_per_sec`, `lora_hash`.
Errors include the full traceback. That's how we debug model behavior later.

## When v2.0 has issues

1. Find the bad outputs in `/var/log/rabbit/server.log` (grep for the prompt_hash)
2. Add the failing cases to training data
3. Retrain LoRA on RunPod (1-2 hrs, ~$15-30)
4. Upload new version to HF as `reattend/rabbit-v2.1`
5. Update `MODEL_REPO` in `rabbit_server.py`, rerun `00_bake_disk.sh`
6. New VMs from now on use v2.1

## Files

```
serving/
├── README.md                    # this file
├── rabbit_server.py             # FastAPI + Unsloth + all signals
├── requirements.txt             # Python deps
├── systemd/
│   ├── rabbit.service           # FastAPI systemd unit
│   ├── auto-stop.service        # auto-stop oneshot
│   └── auto-stop.timer          # 5-min cron timer
├── scripts/
│   ├── install.sh               # runs inside VM during bake
│   └── auto_stop.sh             # the actual idle-kill logic
└── gcp/
    ├── config.sh                # shared env vars
    ├── 00_bake_disk.sh          # one-time: build the image
    ├── vm_spawn.sh              # create/start the Spot VM (rabbit wake)
    ├── vm_stop.sh               # stop the VM (rabbit stop)
    └── vm_status.sh             # state inspector (rabbit status)

cli/
└── rabbit                       # the bash CLI
```
