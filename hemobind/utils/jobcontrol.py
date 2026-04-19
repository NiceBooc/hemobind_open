"""
jobcontrol.py — Poll Schrödinger jobcontrol for job status.
Use this for long-running MD jobs instead of -WAIT.
"""
import subprocess
import time
from pathlib import Path
from hemobind.utils.logger import get_logger

log = get_logger("hemobind.jobcontrol")


def get_job_status(schrodinger: str, job_id: str) -> str:
    """Return 'running', 'completed', 'failed', or 'unknown'."""
    jc = Path(schrodinger) / "jobcontrol"
    result = subprocess.run([str(jc), "-list", job_id], capture_output=True, text=True)
    lines = result.stdout.splitlines()
    if len(lines) < 3:
        return "unknown"
    
    # Line 0 is header, Line 1 is separator, Line 2 is the job
    # But wait, sometimes there are empty lines.
    job_line = ""
    for line in lines:
        if job_id in line and not line.strip().startswith("^"):
            job_line = line
            break
            
    if not job_line:
        return "unknown"
        
    # Columns: JobId, BatchId, Name, Status, ...
    # Status is usually around index 3 or 4.
    # It's better to check the 'Status' column value.
    parts = job_line.split()
    if len(parts) < 4:
        return "unknown"
        
    # For multisim jobs, the Status column is at index 3 or 4 depending on BatchId presence
    # Let's just check the whole line for 'finished' or 'completed' but ONLY if it's not a subjob line
    status_part = job_line.lower()
    if "finished" in status_part or "completed" in status_part:
        return "completed"
    if "died" in status_part or "failed" in status_part:
        return "failed"
    if "running" in status_part or "launched" in status_part or "submitted" in status_part:
        return "running"
        
    return "unknown"


def wait_for_job(schrodinger: str, job_id: str, poll_interval: int = 30,
                 timeout_hours: float = 12.0) -> str:
    """
    Poll until job completes or fails. Returns final status.
    Raises RuntimeError on failure or timeout.
    """
    max_polls = int(timeout_hours * 3600 / poll_interval)
    for i in range(max_polls):
        status = get_job_status(schrodinger, job_id)
        log.info(f"Job {job_id}: {status} (poll {i+1})")
        if status == "completed":
            return "completed"
        if status == "failed":
            raise RuntimeError(f"Job failed: {job_id}")
        time.sleep(poll_interval)
    raise RuntimeError(f"Job timed out after {timeout_hours}h: {job_id}")


def wait_for_all_jobs(schrodinger: str, job_ids: list[str], poll_interval: int = 30) -> None:
    """Wait for multiple jobs to complete (any order)."""
    pending = set(job_ids)
    while pending:
        done = set()
        for jid in list(pending):
            status = get_job_status(schrodinger, jid)
            if status == "completed":
                log.info(f"Job completed: {jid}")
                done.add(jid)
            elif status == "failed":
                raise RuntimeError(f"Job failed: {jid}")
        pending -= done
        if pending:
            time.sleep(poll_interval)
