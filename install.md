# Installing deltapro

## Prerequisites

* **Linux** (RHEL 7+, Ubuntu 18+) or **macOS** (12+) or **Windows** (WSL2)
* `curl` installed
* Your license key from the purchase confirmation email

---

## Install

Run this single command, replacing `YOUR-LICENSE-KEY` with the key Gumroad emailed you:

```sh
curl -fsSL https://deltapro.site/install | sh -s -- YOUR-LICENSE-KEY
```

This will:

1. Detect your OS and architecture automatically
2. Download the right binary for your system
3. Install it to `/usr/local/bin/deltapro`

Verify the install worked:

```sh
deltapro --version
```

---

## Usage

### Save a checkpoint

```sh
deltapro save "timing clean 480MHz"
```

Saves your entire project state with a message. Prints a short ID like `7f3a1c9`.

### List checkpoints

```sh
deltapro list
```

```
7f3a1c9   2024-01-15 14:32   timing clean 480MHz       1.8 GB
3bc9d12   2024-01-15 09:11   pre-constraint tweak       1.7 GB
a1f0023   2024-01-14 22:44   baseline                   1.6 GB
```

### Restore a checkpoint

```sh
deltapro restore 7f3a1c9
```

Restores your project to that exact state in seconds. No recompute, no queue.

### Diff two checkpoints

```sh
deltapro diff 3bc9d12 7f3a1c9
```

Shows exactly what changed between any two saved states.

### Delete a checkpoint

```sh
deltapro delete 3bc9d12
```

### Export a checkpoint as tar.gz

```sh
deltapro export 7f3a1c9 --out ./golden-480mhz.tar.gz
```

Useful for sharing a reproducible state or attaching to a paper.

---

## Ignoring files

Create a `.ckptignore` in your project root to skip logs, temp files, and caches:

```
*.log
*.tmp
sim_work/
__pycache__/
.Xil/
```

Same syntax as `.gitignore`.

---

## Team usage (shared NAS)

Point deltapro at a shared network path so your whole team shares the same rollback history:

```sh
deltapro init --store-path /mnt/nas/projects/soc_verif/.deltapro
```

Everyone on the team can then save and restore from the same store.

---

## Automating saves via TCL hook

Add this to your synthesis TCL script to auto-checkpoint at key milestones:

```tcl
exec deltapro save "post-synth [get_property SLACK [get_timing_paths]]"
```

---

## Uninstall

```sh
sudo rm /usr/local/bin/deltapro
rm -rf .deltapro   # removes the local store for this project
```

---

## Troubleshooting

**`file not found` after install** Your `/usr/local/bin` may not be in `PATH`. Add this to your `~/.bashrc` or `~/.zshrc`:

```sh
export PATH="/usr/local/bin:$PATH"
```

**`Invalid license key` during install** Double-check the key from your Gumroad email. Keys are case-sensitive. If you lost it, log in at [gumroad.com/library](https://gumroad.com/library) to retrieve it.

**Binary permission denied**

```sh
chmod +x /usr/local/bin/deltapro
```

**On macOS — `cannot be opened because the developer cannot be verified`**

```sh
xattr -d com.apple.quarantine /usr/local/bin/deltapro
```

---

## Support

Email: support@deltapro.site
14-day no-questions refund guaranteed.
