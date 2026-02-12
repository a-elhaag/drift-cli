"""History and snapshot management with improved safety and performance."""

import json
import shutil
from datetime import datetime
from pathlib import Path
from typing import List, Optional
from uuid import uuid4

from drift_cli.models import HistoryEntry, Plan


class HistoryManager:
    """Manages command history and file snapshots with size limits and rotation."""
    
    MAX_HISTORY_SIZE_MB = 10  # Max size for history.jsonl before rotation
    MAX_CONTEXT_SIZE_MB = 5   # Max size for context.json before cleanup

    def __init__(self, drift_dir: Optional[Path] = None):
        self.drift_dir = drift_dir or Path.home() / ".drift"
        self.history_file = self.drift_dir / "history.jsonl"
        self.snapshots_dir = self.drift_dir / "snapshots"

        # Ensure directories exist
        self.drift_dir.mkdir(exist_ok=True)
        self.snapshots_dir.mkdir(exist_ok=True)
        
        # Auto-rotate large files
        self._rotate_if_needed()

    def _rotate_if_needed(self):
        """Rotate history file if it exceeds size limit."""
        if not self.history_file.exists():
            return
        
        file_size_mb = self.history_file.stat().st_size / (1024 * 1024)
        
        if file_size_mb > self.MAX_HISTORY_SIZE_MB:
            # Rotate: keep last 50% of entries
            try:
                with open(self.history_file, 'r') as f:
                    lines = f.readlines()
                
                # Keep newer half
                keep_from = len(lines) // 2
                
                # Archive old entries
                archive_file = self.drift_dir / f"history.{datetime.now().strftime('%Y%m%d_%H%M%S')}.jsonl"
                with open(archive_file, 'w') as f:
                    f.writelines(lines[:keep_from])
                
                # Rewrite current history with newer entries
                with open(self.history_file, 'w') as f:
                    f.writelines(lines[keep_from:])
            except Exception:
                # If rotation fails, don't break the app
                pass
    
    def _validate_path_safety(self, path: Path, allowed_roots: List[Path]) -> bool:
        """
        Validate that a path is within allowed root directories.
        
        Prevents path traversal attacks.
        
        Args:
            path: Path to validate
            allowed_roots: List of allowed root directories
            
        Returns:
            True if path is safe, False otherwise
        """
        try:
            resolved = path.resolve()
            
            # Check if path is within any allowed root
            for root in allowed_roots:
                try:
                    resolved.relative_to(root.resolve())
                    return True
                except ValueError:
                    continue
            
            return False
        except (OSError, RuntimeError):
            # Path resolution failed (e.g., too many symlinks)
            return False

    def add_entry(
        self,
        query: str,
        plan: Plan,
        executed: bool = False,
        exit_code: Optional[int] = None,
        snapshot_id: Optional[str] = None,
    ) -> HistoryEntry:
        """Add an entry to the history."""
        entry = HistoryEntry(
            timestamp=datetime.now().isoformat(),
            query=query,
            plan=plan,
            executed=executed,
            exit_code=exit_code,
            snapshot_id=snapshot_id,
        )

        with open(self.history_file, "a") as f:
            f.write(entry.model_dump_json() + "\n")

        return entry

    def get_history(self, limit: int = 10) -> List[HistoryEntry]:
        """Get recent history entries."""
        if not self.history_file.exists():
            return []

        entries = []
        with open(self.history_file, "r") as f:
            lines = f.readlines()
            for line in reversed(lines[-limit:]):
                try:
                    data = json.loads(line)
                    entries.append(HistoryEntry(**data))
                except (json.JSONDecodeError, ValueError):
                    continue

        return entries

    def get_last_entry(self) -> Optional[HistoryEntry]:
        """Get the most recent history entry."""
        entries = self.get_history(limit=1)
        return entries[0] if entries else None

    def create_snapshot(self, files: List[str]) -> str:
        """
        Create a snapshot of files before modification.

        Args:
            files: List of file paths to snapshot

        Returns:
            Snapshot ID (UUID)
        """
        snapshot_id = str(uuid4())
        snapshot_dir = self.snapshots_dir / snapshot_id
        snapshot_dir.mkdir()

        metadata = {
            "id": snapshot_id,
            "timestamp": datetime.now().isoformat(),
            "files": [],
            "size_bytes": 0,
        }

        total_size = 0
        for file_path in files:
            path = Path(file_path).expanduser().resolve()
            
            # Validate file exists
            if not path.exists():
                continue
                
            # Skip if not a regular file
            if not path.is_file():
                continue
                
            # Create relative path structure in snapshot
            try:
                rel_path = path.relative_to(Path.home())
                target = snapshot_dir / rel_path
            except ValueError:
                # File is outside home directory
                target = snapshot_dir / "external" / path.name

            target.parent.mkdir(parents=True, exist_ok=True)
            
            try:
                shutil.copy2(path, target)
                file_size = path.stat().st_size
                total_size += file_size
                metadata["files"].append({
                    "original": str(path),
                    "snapshot": str(target),
                    "size_bytes": file_size
                })
            except (OSError, IOError) as e:
                # Silently skip files that can't be snapshotted
                pass

        metadata["size_bytes"] = total_size

        # Save metadata
        with open(snapshot_dir / "metadata.json", "w") as f:
            json.dump(metadata, f, indent=2)

        return snapshot_id

    def restore_snapshot(self, snapshot_id: str) -> bool:
        """
        Restore files from a snapshot with improved path validation.

        Args:
            snapshot_id: The snapshot ID to restore

        Returns:
            True if successful, False otherwise
        """
        # Validate snapshot_id format to prevent path traversal
        if not snapshot_id or '/' in snapshot_id or '\\' in snapshot_id or snapshot_id.startswith('.'):
            return False
        
        snapshot_dir = self.snapshots_dir / snapshot_id
        metadata_file = snapshot_dir / "metadata.json"

        if not snapshot_dir.exists() or not metadata_file.exists():
            return False

        try:
            with open(metadata_file, "r") as f:
                metadata = json.load(f)

            restored_count = 0
            allowed_roots = [Path.home(), self.snapshots_dir]
            
            for file_info in metadata["files"]:
                original_str = file_info.get("original")
                snapshot_str = file_info.get("snapshot")
                
                if not original_str or not snapshot_str:
                    continue
                
                original = Path(original_str).expanduser().resolve()
                snapshot = Path(snapshot_str).resolve()

                # Enhanced path traversal protection
                if not self._validate_path_safety(snapshot, [self.snapshots_dir]):
                    continue  # Skip files outside snapshot directory
                
                if not self._validate_path_safety(original, [Path.home()]):
                    continue  # Skip files outside home directory

                if snapshot.exists() and snapshot.is_file():
                    original.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(snapshot, original)
                    restored_count += 1

            return restored_count > 0
        except (json.JSONDecodeError, KeyError, OSError):
            return False

    def list_snapshots(self) -> List[dict]:
        """List all available snapshots."""
        snapshots = []
        for snapshot_dir in self.snapshots_dir.iterdir():
            if not snapshot_dir.is_dir():
                continue

            metadata_file = snapshot_dir / "metadata.json"
            if metadata_file.exists():
                try:
                    with open(metadata_file, "r") as f:
                        metadata = json.load(f)
                        snapshots.append(metadata)
                except Exception:
                    continue

        return sorted(snapshots, key=lambda x: x["timestamp"], reverse=True)

    def cleanup_old_snapshots(self, keep: int = 10, max_age_days: int = 30) -> int:
        """
        Clean up old snapshots to save disk space.

        Args:
            keep: Minimum number of recent snapshots to keep
            max_age_days: Delete snapshots older than this many days

        Returns:
            Number of snapshots deleted
        """
        snapshots = self.list_snapshots()
        deleted = 0

        if len(snapshots) <= keep:
            return 0

        from datetime import timedelta
        cutoff_time = datetime.now() - timedelta(days=max_age_days)

        for idx, snapshot in enumerate(snapshots):
            # Always keep the 'keep' most recent
            if idx < keep:
                continue

            # Check age
            try:
                snap_time = datetime.fromisoformat(snapshot["timestamp"])
                if snap_time < cutoff_time:
                    snapshot_dir = self.snapshots_dir / snapshot["id"]
                    shutil.rmtree(snapshot_dir)
                    deleted += 1
            except Exception:
                pass

        return deleted
