"""
fileio.py — PDB/MAE/PDBQT sanitization helpers.
Adapted from Docking/scripts/sanitize_pdb.py
"""
from pathlib import Path


def sanitize_pdb(input_pdb: str | Path, output_pdb: str | Path, res_name: str = "LIG") -> None:
    """
    Fix duplicate atom names and serial numbers in PDB files produced by
    AutoDock-GPU / OpenBabel. Required before feeding to any Schrödinger tool.
    """
    input_pdb, output_pdb = Path(input_pdb), Path(output_pdb)
    lines = input_pdb.read_text().splitlines()

    new_lines = []
    atom_count = 1
    elem_counts: dict[str, int] = {}

    for line in lines:
        if line.startswith("ATOM") or line.startswith("HETATM"):
            elem = line[76:78].strip()
            if not elem:
                elem = line[12:14].strip()
            elem = "".join(c for c in elem if c.isalpha()) or "X"

            count = elem_counts.get(elem, 0) + 1
            elem_counts[elem] = count
            name = f"{elem}{count}"[:4]

            new_line = list(line.ljust(80))
            new_line[0:6] = list("HETATM")
            new_line[6:11] = list(f"{atom_count:5}")
            new_line[12:16] = list(f" {name:<3}" if len(name) < 4 else name[:4])
            new_line[17:20] = list(f"{res_name:3}")
            new_lines.append("".join(new_line))
            atom_count += 1
        elif line.startswith(("CONECT", "MASTER", "END", "MODEL")):
            continue
        else:
            new_lines.append(line)

    output_pdb.write_text("\n".join(new_lines) + "\n")


def strip_receptor_pdb(input_pdb: str | Path, output_pdb: str | Path,
                       remove_resnames: tuple = ("HOH", "NMA", "WAT")) -> None:
    """Strip solvent and unwanted HETATM residues from receptor PDB."""
    lines = Path(input_pdb).read_text().splitlines()
    kept = []
    for line in lines:
        if line.startswith("HETATM"):
            resname = line[17:20].strip()
            if resname in remove_resnames:
                continue
        kept.append(line)
    Path(output_pdb).write_text("\n".join(kept) + "\n")
