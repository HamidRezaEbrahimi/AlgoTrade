# backend/scratch/copy_skill_to_alef.py
from pathlib import Path
import shutil

src = Path("G:/Projects/AlgoTrade/.agents/skills/hybrid-wave-ml-training/SKILL.md")
dest_dir = Path("G:/Projects/AlefTrade/.agents/skills/hybrid-wave-ml-training")
dest_dir.mkdir(parents=True, exist_ok=True)
dest = dest_dir / "SKILL.md"

shutil.copy2(src, dest)
print(f"Copied successfully to {dest}")
