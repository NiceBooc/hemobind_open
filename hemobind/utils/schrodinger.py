"""
schrodinger.py — Subprocess wrappers for Schrödinger utilities.

KEY RULES (learned from debugging):
- Always run multisim from within the directory containing the MSJ and CMS files.
- Never pass absolute paths to -m or the input CMS — use filenames only.
- Use -WAIT for short jobs (prepwizard, system builder).
- For long MD jobs, use polling via jobcontrol.py instead of -WAIT.
- Do NOT pass -c <cfg_file> to multisim — embed all params in the MSJ.
"""
import subprocess
import os
from pathlib import Path
from hemobind.utils.logger import get_logger

log = get_logger("hemobind.schrodinger")


def run_prepwizard(schrodinger: str, input_file: Path, output_file: Path,
                   ph: float = 7.0, fillsidechains: bool = True) -> None:
    """Run PrepWizard synchronously. Both paths must be in the same directory."""
    prepwiz = Path(schrodinger) / "utilities" / "prepwizard"
    cmd = [str(prepwiz), "-WAIT", "-fix"]
    if fillsidechains:
        cmd.append("-fillsidechains")
    cmd += [f"-propka_pH", str(ph), str(input_file.name), str(output_file.name)]

    log.info(f"PrepWizard: {input_file.name} → {output_file.name}")
    result = subprocess.run(cmd, cwd=str(input_file.parent), capture_output=True, text=True)
    if result.returncode != 0:
        log.error(f"PrepWizard failed:\n{result.stderr}")
        raise RuntimeError(f"PrepWizard failed for {input_file}")
    if not output_file.exists():
        raise RuntimeError(f"PrepWizard produced no output: {output_file}")
    log.info(f"PrepWizard done: {output_file.name} ({output_file.stat().st_size // 1024} KB)")


def run_multisim(schrodinger: str, jobname: str, msj_file: Path,
                 input_cms: Path, output_cms: Path | None = None,
                 subhost: str | None = None, extra_args: list[str] | None = None) -> str:
    """
    Run multisim synchronously (-WAIT). Must be called with cwd = dir containing MSJ and CMS.
    Returns job ID string.
    """
    multisim = Path(schrodinger) / "utilities" / "multisim"
    cmd = [str(multisim), "-WAIT", "-JOBNAME", jobname, "-maxjob", "1",
           "-m", msj_file.name]
    if output_cms:
        cmd += ["-o", output_cms.name]
    if subhost:
        cmd += ["-SUBHOST", subhost]
    if extra_args:
        cmd += extra_args
    cmd.append(input_cms.name)

    cwd = str(msj_file.parent)
    log.info(f"multisim [{jobname}]: {' '.join(cmd)}")
    result = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True)

    # Extract job ID from output
    job_id = ""
    for line in result.stdout.splitlines():
        if line.startswith("JobId:"):
            job_id = line.split(":", 1)[1].strip()

    if result.returncode != 0:
        log.error(f"multisim failed [{jobname}]:\n{result.stderr}\n{result.stdout}")
        raise RuntimeError(f"multisim failed: {jobname}")

    log.info(f"multisim done [{jobname}], job_id={job_id}")
    return job_id


def structconvert(schrodinger: str, input_file: Path, output_file: Path) -> None:
    """Convert between chemical file formats."""
    conv = Path(schrodinger) / "utilities" / "structconvert"
    result = subprocess.run([str(conv), str(input_file), str(output_file)],
                            capture_output=True, text=True)
    if result.returncode != 0 or not output_file.exists():
        raise RuntimeError(f"structconvert failed: {result.stderr}")
