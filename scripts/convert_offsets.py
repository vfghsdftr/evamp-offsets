"""Convert a literal-only C++ offset dump to JSON without compiling or executing it."""

import argparse
import hashlib
import json
from pathlib import Path
import re

VERSION = re.compile(r'inline\s+(?:const\s+)?std::string\s+ClientVersion\s*=\s*"(version-[0-9a-f]{16})"\s*;')
FIELD = re.compile(r'(?:inline\s+)?(?:constexpr\s+|const\s+)?(?:std::)?uintptr_t\s+(\w+)\s*=\s*(0x[0-9a-fA-F]+|[0-9]+)\s*;')
NAMESPACE = re.compile(r'namespace\s+(\w+)\s*\{')


def convert(text):
    if len(text.encode("utf-8")) > 4 * 1024 * 1024:
        raise ValueError("Header exceeds 4 MiB")
    groups, stack = {}, []
    version, root_seen, root_closed = None, False, False
    for line_number, original in enumerate(text.splitlines(), 1):
        line = original.strip()
        # This dump uses standalone /* banner lines without closing comment markers.
        if not line or line.startswith(("#", "//", "/*", "*")):
            continue
        line = line.split("//", 1)[0].strip()
        namespace = NAMESPACE.fullmatch(line)
        if namespace:
            name = namespace[1]
            if not stack:
                if name != "Offsets" or root_seen:
                    raise ValueError(f"Line {line_number}: expected one Offsets namespace")
                root_seen = True
            elif len(stack) == 1:
                if name in groups:
                    raise ValueError(f"Line {line_number}: duplicate group {name}")
                groups[name] = {}
            else:
                raise ValueError(f"Line {line_number}: nested groups are unsupported")
            stack.append(name)
            continue
        if line in ("}", "};"):
            if not stack:
                raise ValueError(f"Line {line_number}: unmatched closing brace")
            stack.pop()
            root_closed = not stack
            continue
        match = VERSION.fullmatch(line)
        if match and stack == ["Offsets"] and version is None:
            version = match[1]
            continue
        match = FIELD.fullmatch(line)
        if match and len(stack) == 2:
            name, literal = match.groups()
            value = int(literal, 16 if literal.startswith("0x") else 10)
            if value > 0x7FFFFFFF or name in groups[stack[-1]]:
                raise ValueError(f"Line {line_number}: duplicate or out-of-range field {name}")
            groups[stack[-1]][name] = value
            continue
        raise ValueError(f"Line {line_number}: unsupported declaration; use literal integer offsets")
    count = sum(len(fields) for fields in groups.values())
    if stack or not root_seen or not root_closed or not version or not count:
        raise ValueError("Incomplete header: version, balanced namespaces and offsets are required")
    declared_versions = re.findall(r"Roblox Version\s*:\s*(version-[0-9a-f]{16})", text)
    if any(declared != version for declared in declared_versions):
        raise ValueError("Banner version does not match ClientVersion")
    declared_counts = re.findall(r"Total Offsets\s*:\s*(\d+)", text)
    if any(int(declared) != count for declared in declared_counts):
        raise ValueError(f"Header is incomplete: parsed {count} offsets, banner declares {declared_counts}")
    return {"Roblox Version": version, "Total Offsets": count,
            "Source SHA256": hashlib.sha256(text.encode("utf-8")).hexdigest(), "Offsets": groups}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("header", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    try:
        if args.header.stat().st_size > 4 * 1024 * 1024:
            raise ValueError("Header exceeds 4 MiB")
        result = convert(args.header.read_text(encoding="utf-8-sig"))
    except (ValueError, OSError) as error:
        parser.exit(1, f"Offset conversion failed: {error}\n")
    temporary = args.output.with_suffix(args.output.suffix + ".tmp")
    temporary.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    temporary.replace(args.output)
    print(f"Published {result['Total Offsets']} offsets for {result['Roblox Version']}")


if __name__ == "__main__":
    main()
