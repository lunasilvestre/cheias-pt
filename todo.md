**R2 Sync** (run before Prompt B)
```bash
cd ~/Documents/dev/cheias-pt
rclone sync data/cog/satellite-ir/ r2:cheias-cog/cog/satellite-ir/ --progress  # 101MB, 48 files
rclone sync data/cog/mslp/ r2:cheias-cog/cog/mslp/ --progress                 # 31MB, 408 files
rclone sync data/cog/wind-u/ r2:cheias-cog/cog/wind-u/ --progress             # 34MB, 408 files
rclone sync data/cog/wind-v/ r2:cheias-cog/cog/wind-v/ --progress             # 35MB, 408 files
```
~200MB total. Can run in parallel while reviewing Prompt A results.

**Prompt B — Titiler + Satellite + MSLP** (after sync)
- Migrates all rasters from local PNGs → titiler tile endpoints
- Adds satellite IR animation (49 hourly frames) + temporal MSLP
- Adds dynamic colormap dropdown + titiler attribution
- ```bash
  cat prompts/eye-candy-B-titiler-satellite-mslp.md | claude



  