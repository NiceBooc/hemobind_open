import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path

@dataclass
class CheckResult:
    ok: bool
    version: str = "Unknown"
    message: str = ""

class DependencyChecker:
    @staticmethod
    def check_command(cmd: list[str]) -> CheckResult:
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=5)
            if result.returncode == 0:
                # Try to extract version from output
                version = result.stdout.strip().split('\n')[0] if result.stdout else "Available"
                return CheckResult(True, version)
            return CheckResult(False, message=result.stderr.strip())
        except Exception as e:
            return CheckResult(False, message=str(e))

    @staticmethod
    def check_path(path: str, subpath: str = "") -> CheckResult:
        p = Path(path)
        if subpath:
            p = p / subpath
        if p.exists():
            return CheckResult(True, message=str(p))
        return CheckResult(False, message=f"Path not found: {p}")

    @staticmethod
    def check_python_module(module_name: str) -> CheckResult:
        try:
            import importlib
            mod = importlib.import_module(module_name)
            version = getattr(mod, "__version__", "Available")
            return CheckResult(True, version)
        except ImportError as e:
            return CheckResult(False, message=str(e))

    def check_all(self, config_paths: dict = None) -> dict[str, CheckResult]:
        config_paths = config_paths or {}
        results = {}
        
        # Tools in PATH
        results["obabel"] = self.check_command(["obabel", "-V"])
        results["adgpu"] = self.check_command(["adgpu", "--version"])
        results["docker"] = self.check_command(["docker", "info"])
        
        # Python Modules (OpenMM Stack)
        results["openmm"] = self.check_python_module("openmm")
        results["pdbfixer"] = self.check_python_module("pdbfixer")
        results["openff"] = self.check_python_module("openff.toolkit")
        
        return results
