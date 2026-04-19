"""
cli.py — Entry point for HemoBind CLI.
"""
import argparse
from pathlib import Path
from datetime import datetime
import shutil

from hemobind.config import load_config
from hemobind.pipeline import Pipeline, STAGES
from hemobind.utils.logger import get_logger


def main():
    parser = argparse.ArgumentParser(description="HemoBind: Automated MD-validated docking pipeline.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    # RUN command
    run_parser = subparsers.add_parser("run", help="Run the pipeline")
    run_parser.add_argument("--config", required=True, help="Path to config.yaml")
    run_parser.add_argument("--from", dest="from_stage", choices=STAGES, help="Start from this stage")
    run_parser.add_argument("--to", dest="to_stage", choices=STAGES, help="Stop after this stage")

    # STATUS command
    status_parser = subparsers.add_parser("status", help="Check status of a run directory")
    status_parser.add_argument("run_dir", help="Path to the run directory")

    # CLEAN command
    clean_parser = subparsers.add_parser("clean", help="Clean intermediate files to save space")
    clean_parser.add_argument("run_dir", help="Path to the run directory")

    args = parser.parse_args()

    if args.command == "run":
        config = load_config(args.config)
        
        # Resolve run_dir
        run_dir_str = config.output_dir
        if "{timestamp}" in run_dir_str:
            ts = datetime.now().strftime("%Y-%m-%d_%H-%M")
            run_dir_str = run_dir_str.replace("{timestamp}", ts)
        run_dir = Path(run_dir_str).resolve()
        
        pipeline = Pipeline(config, run_dir)
        pipeline.run(from_stage=args.from_stage, to_stage=args.to_stage)

    elif args.command == "status":
        run_dir = Path(args.run_dir)
        if not run_dir.exists():
            print(f"Run directory not found: {run_dir}")
            return
        
        print(f"Status for: {run_dir}")
        for stage in STAGES:
            if (run_dir / f"{stage}.done").exists():
                print(f"  [DONE] {stage}")
            else:
                print(f"  [PENDING] {stage}")

    elif args.command == "clean":
        run_dir = Path(args.run_dir)
        if not run_dir.exists():
            print(f"Run directory not found: {run_dir}")
            return
            
        print(f"Cleaning intermediate files in {run_dir}...")
        count = 0
        
        # Clean tgz files
        for tgz in run_dir.rglob("*.tgz"):
            tgz.unlink()
            count += 1
            
        # Clean Desmond scratch dirs
        for d in run_dir.rglob("*_build_[0-9]"):
            if d.is_dir():
                shutil.rmtree(d)
                count += 1
                
        for d in run_dir.rglob("*_md_[0-9]"):
            if d.is_dir():
                shutil.rmtree(d)
                count += 1
                
        print(f"Cleaned {count} items. Space recovered.")


if __name__ == "__main__":
    main()
