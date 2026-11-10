"""Bundle only application sources, assets and instructions, never local data."""
from pathlib import Path
import zipfile

source = Path(__file__).resolve().parent
root = source.parent
out = root / "output" / "desktop"
out.mkdir(parents=True, exist_ok=True)
target = out / "Otoskop-Windows-Quellpaket.zip"
with zipfile.ZipFile(target, "w", compression=zipfile.ZIP_DEFLATED) as archive:
    for path in sorted(source.rglob("*")):
        if path.is_file() and "__pycache__" not in path.parts and path.suffix.lower() in {
            ".py", ".md", ".txt", ".bat", ".command", ".spec", ".png", ".ico", ".icns", ".bin", ".json"
        }:
            archive.write(path, str(Path("Otoskop") / path.relative_to(root)))
    for path in sorted((root / "firmware" / "Otoskop").glob("*")):
        if path.is_file() and path.suffix in {".ino", ".h"}:
            archive.write(path, str(Path("Otoskop") / path.relative_to(root)))
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
