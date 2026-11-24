"""Bundle only application sources, assets and instructions, never local data."""
from pathlib import Path
import zipfile
import runpy

source = Path(__file__).resolve().parent
root = source.parent
out = root / "output" / "desktop"
out.mkdir(parents=True, exist_ok=True)
version = runpy.run_path(str(source / "otoskop" / "__init__.py"))["__version__"]
target = out / f"Otoskop-{version}-Windows-Quellpaket.zip"
with zipfile.ZipFile(target, "w", compression=zipfile.ZIP_DEFLATED) as archive:
    for path in sorted(source.rglob("*")):
        if path.is_file() and "__pycache__" not in path.parts and path.suffix.lower() in {
            ".py", ".md", ".txt", ".bat", ".command", ".spec", ".png", ".ico", ".icns", ".bin", ".json"
        }:
            archive.write(path, str(Path("Otoskop") / path.relative_to(root)))
    for path in sorted((root / "firmware" / "Otoskop").glob("*")):
        if path.is_file() and path.suffix in {".ino", ".h"}:
            archive.write(path, str(Path("Otoskop") / path.relative_to(root)))
    for name in ("README.md", "KURZUEBERBLICK.txt", "REQUIREMENTS.md", "HARDWARELISTE.md", "HARDWARELISTE.csv",
                 "hardware/ERGAENZUNGEN_2.0.md", "hardware/README.md",
                 "hardware/Otoskop_2.0.0_Testaufbau.pdf", "hardware/Otoskop_2.0.0_Testaufbau.svg",
                 "hardware/Otoskop_2.0.0_Drahtliste.csv", "hardware/Otoskop_2.0.0_Netzliste.csv",
                 "hardware/Otoskop_2.0.0_Netze.json", "hardware/settings_reference.h",
                 "hardware/generate_schematic.py", "docs/VERIFIKATION.md"):
        archive.write(root / name, str(Path("Otoskop") / name))
    archive.writestr("Otoskop/START_HIER.txt",
                     "Otoskop fuer Windows\n\n"
                     "1. Python 3.10 bis 3.14 (64 Bit) mit Python-Launcher installieren.\n"
                     "2. Dieses ZIP vollstaendig entpacken.\n"
                     "3. desktop\\Start-Otoskop.bat doppelklicken.\n\n"
                     "Beim ersten Start werden Qt-Bibliotheken ueber das Internet geladen.\n"
                     "Danach ist kein Internetzugang erforderlich.\n"
                     "Ohne Hardware oben rechts Demo einschalten.\n"
                     "DE / EN wechselt die Sprache. Das Fragezeichen oben rechts oder F1 hilft beim Verbinden.\n"
                     "Weitere Hinweise und EXE-Paketbau: desktop\\README.md\n\n"
                     "Der Windows-Start muss noch auf einem Windows-Rechner geprueft werden.\n")
print(target)
