"""Build the checked-in Material Symbols subset used by the application.

Requires FontTools with WOFF support. The source font comes from the installed
material-symbols package; icon names are discovered from the TSX source.
"""

from pathlib import Path
import re

from fontTools import subset
from fontTools.ttLib import TTFont


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "node_modules" / "material-symbols" / "material-symbols-outlined.woff2"
OUTPUT = ROOT / "src" / "app" / "material-symbols-outlined-subset.woff2"
PATTERNS = (
    re.compile(r'data-icon="([a-z0-9_]+)"'),
    re.compile(r'icon:\s*["\']([a-z0-9_]+)["\']'),
)
MATERIAL_SPAN = re.compile(
    r'<span[^>]*material-symbols-outlined[^>]*>(.*?)</span>', re.DOTALL
)


def icon_names():
    names = set()
    for source in (ROOT / "src").rglob("*.tsx"):
        text = source.read_text(encoding="utf-8")
        if "material-symbols-outlined" not in text and "icon:" not in text:
            continue
        for pattern in PATTERNS:
            for match in pattern.finditer(text):
                names.update(value for value in match.groups() if value)
        for match in MATERIAL_SPAN.finditer(text):
            names.update(re.findall(r'["\']([a-z][a-z0-9_]+)["\']', match.group(1)))
            literal = match.group(1).strip()
            if re.fullmatch(r"[a-z][a-z0-9_]+", literal):
                names.add(literal)
    return names


def ligature_outputs(font, names):
    cmap = font.getBestCmap()
    wanted = {tuple(cmap[ord(char)] for char in name): name for name in names}
    outputs = {}
    for lookup in font["GSUB"].table.LookupList.Lookup:
        tables = []
        if lookup.LookupType == 4:
            tables = lookup.SubTable
        elif lookup.LookupType == 7:
            tables = [table.ExtSubTable for table in lookup.SubTable if table.ExtensionLookupType == 4]
        for table in tables:
            for first, ligatures in table.ligatures.items():
                for ligature in ligatures:
                    sequence = (first, *ligature.Component)
                    if sequence in wanted:
                        outputs[wanted[sequence]] = ligature.LigGlyph
    missing = names - outputs.keys()
    if missing:
        raise RuntimeError(f"Material Symbols not found: {', '.join(sorted(missing))}")
    return outputs


def main():
    names = icon_names()
    font = TTFont(SOURCE)
    outputs = ligature_outputs(font, names)
    options = subset.Options()
    options.flavor = "woff2"
    options.layout_features = ["liga"]
    options.name_IDs = [0, 1, 2, 3, 4, 5, 6]
    subsetter = subset.Subsetter(options=options)
    subsetter.populate(text="".join(sorted(set("".join(names)))), glyphs=list(outputs.values()))
    subsetter.subset(font)
    font.save(OUTPUT)
    print(f"Wrote {OUTPUT} with {len(names)} icons ({OUTPUT.stat().st_size} bytes)")


if __name__ == "__main__":
    main()
