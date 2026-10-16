#!/usr/bin/env python3
"""Validate source catalogs and generate a static, content-addressed Pages artifact."""
import argparse
import hashlib
import json
import math
from pathlib import Path
from urllib.parse import urlsplit

MAX_BYTES = 12 * 1024 * 1024
FILES = {
    "postcards": "postcard-spots.json",
    "accessories": "pure-points-category-updatable.json",
}


def require(condition, message):
    if not condition:
        raise ValueError(message)


def text(value):
    return isinstance(value, str) and bool(value.strip())


def strings(value):
    return isinstance(value, list) and all(isinstance(item, str) for item in value)


def secure_url(value):
    if not isinstance(value, str):
        return False
    url = urlsplit(value)
    return url.scheme.lower() == "https" and bool(url.hostname) and url.username is None and url.password is None


def coordinate(record):
    for key, limit in (("lat", 90), ("lng", 180)):
        number = record.get(key)
        require(type(number) in (int, float) and math.isfinite(number) and abs(number) <= limit,
                f"Invalid {key}: {number}")


def validate(kind, value):
    require(isinstance(value, dict) and type(value.get("schemaVersion")) is int
            and value["schemaVersion"] == 1, "Unsupported schemaVersion")
    if kind == "postcards":
        require(secure_url(value.get("sourceURL")), "Invalid catalog sourceURL")
        require(isinstance(value.get("sourceRevision"), str) and isinstance(value.get("importedAt"), str),
                "Missing postcard metadata")
        spots = value.get("spots")
        require(isinstance(spots, list) and bool(spots), "Empty postcard catalog")
        ids = set()
        for spot in spots:
            require(isinstance(spot, dict), "Invalid spot")
            require(all(text(spot.get(key)) for key in ("id", "name", "country")), "Missing spot identity")
            require(spot["id"] not in ids, f"Duplicate spot ID: {spot['id']}")
            ids.add(spot["id"])
            require(type(spot.get("nameIsApproximate")) is bool, "Missing nameIsApproximate")
            require(spot.get("type") in ("flower", "mushroom"), "Unknown postcard type")
            require(all(isinstance(spot.get(key), str) for key in ("countryCode", "city", "capturedAt")),
                    "Missing spot metadata")
            require(strings(spot.get("keywords")), "Invalid keywords")
            require(secure_url(spot.get("sourceURL")), "Invalid spot sourceURL")
            require(spot.get("imageURL") is None or secure_url(spot["imageURL"]), "Invalid imageURL")
            coordinate(spot)
    else:
        require(all(isinstance(value.get(key), str) for key in ("regionCode", "updatedAt", "coverage")),
                "Missing accessory metadata")
        categories, points = value.get("categories"), value.get("points")
        require(isinstance(categories, dict) and bool(categories), "Empty accessory categories")
        require(isinstance(points, dict) and bool(points), "Empty accessory points")
        for key, point in points.items():
            require(text(key) and isinstance(point, dict), "Invalid point")
            require(text(point.get("city")) and text(point.get("area")), "Missing point region")
            coordinate(point)
        for key, category in categories.items():
            require(text(key) and isinstance(category, dict) and text(category.get("name")), "Invalid category")
            icon = category.get("icon")
            require(icon is None or (text(icon) and len(icon) <= 8), "Invalid category icon")
            ids = category.get("pointIds")
            require(strings(ids) and len(set(ids)) == len(ids), "Invalid or duplicate point references")
            require(all(item in points for item in ids), "Missing referenced point")


def build(source, output):
    # Validate every input before publishing any file.
    payloads = {}
    manifest = {"schemaVersion": 1, "catalogs": {}}
    for kind, filename in FILES.items():
        data = (source / filename).read_bytes()
        require(0 < len(data) <= MAX_BYTES, f"Catalog size out of range: {filename}")
        validate(kind, json.loads(data))
        digest = hashlib.sha256(data).hexdigest()
        name = f"{kind}-{digest}.json"
        payloads[name] = data
        manifest["catalogs"][kind] = {
            "version": digest[:16], "schemaVersion": 1,
            "file": name, "byteCount": len(data), "sha256": digest,
        }
    target = output / "catalog"
    target.mkdir(parents=True, exist_ok=True)
    for name, data in payloads.items():
        (target / name).write_bytes(data)
    # Publish immutable payloads first; the manifest is the final pointer.
    temporary = target / "manifest.json.tmp"
    temporary.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    temporary.replace(target / "manifest.json")
    (output / ".nojekyll").touch()
    (output / "index.html").write_text(
        '<!doctype html><meta charset="utf-8"><title>HappyFly Data</title>'
        '<p>HappyFly 地點資料：<a href="catalog/manifest.json">版本清單</a></p>\n', encoding="utf-8")
    print(f"Validated and exported {len(payloads)} catalogs to {target}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-dir", type=Path, default=Path(__file__).resolve().parents[1] / "HappyFly/Resources")
    parser.add_argument("--output-dir", type=Path, default=Path(__file__).resolve().parents[1] / "build/catalog-site")
    args = parser.parse_args()
    try:
        build(args.source_dir, args.output_dir)
    except (ValueError, TypeError, KeyError) as error:
        parser.exit(1, f"Catalog validation failed: {error}\n")
