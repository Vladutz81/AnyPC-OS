#!/usr/bin/env python3
"""Publish the installer OCI payload to the read-only AnyPC registry on a static site."""

import argparse
import hashlib
import json
import os
import re
import shutil
import subprocess
import tempfile
from pathlib import Path

DIGEST = re.compile(r"sha256:[0-9a-f]{64}")
TYPES = {"application/vnd.oci.image.manifest.v1+json",
         "application/vnd.docker.distribution.manifest.v2+json"}


def publish(source, webroot, tag):
    if not re.fullmatch(r"[a-z][a-z0-9_-]{0,31}", tag):
        raise ValueError("Invalid update tag")
    if source.is_dir():
        publish_layout(source, webroot, tag)
        return
    with tempfile.TemporaryDirectory(prefix=".publish-", dir=webroot.parent) as staging:
        layout = Path(staging) / "oci"
        subprocess.run(["xorriso", "-osirrox", "on", "-indev", str(source), "-extract",
                        "/container", str(layout)], check=True)
        publish_layout(layout, webroot, tag)


def publish_layout(layout, webroot, tag):
    registry = webroot / "v2"
    blobs = registry / "anypc-os/blobs"
    manifests = registry / "anypc-os/manifests"
    for folder in (blobs, manifests):
        folder.mkdir(parents=True, exist_ok=True)
    (registry / "index.html").write_text("{}\n")
    entries = json.loads((layout / "index.json").read_text())["manifests"]
    if len(entries) != 1:
        raise ValueError("Expected one x86-64 system image")

    def verified(descriptor):
        digest = descriptor["digest"]
        if not DIGEST.fullmatch(digest):
            raise ValueError("Invalid digest in the image")
        path = layout / "blobs/sha256" / digest[7:]
        with path.open("rb") as stream:
            actual = hashlib.file_digest(stream, "sha256").hexdigest()
        if actual != digest[7:] or path.stat().st_size != descriptor["size"]:
            raise ValueError(f"Corrupted blob {digest}")
        return path

    descriptor = entries[0]
    if descriptor["mediaType"] not in TYPES:
        raise ValueError("Unsupported manifest type")
    manifest = verified(descriptor)
    body = json.loads(manifest.read_text())
    for entry in [body["config"], *body["layers"]]:
        path = verified(entry)
        target = blobs / entry["digest"]
        if not target.exists():
            os.link(path, target)
    digest_path = manifests / descriptor["digest"]
    if not digest_path.exists():
        os.link(manifest, digest_path)
    # Replace the tag only after every object is available to existing and new clients.
    with tempfile.NamedTemporaryFile(dir=manifests, delete=False) as output:
        with manifest.open("rb") as source:
            shutil.copyfileobj(source, output)
        os.fchmod(output.fileno(), 0o644)
    os.replace(output.name, manifests / tag)
    print(descriptor["mediaType"], descriptor["digest"])


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path, help="installer ISO or its prepared OCI layout")
    parser.add_argument("webroot", type=Path)
    parser.add_argument("--tag", default="stable")
    args = parser.parse_args()
    publish(args.source.resolve(strict=True), args.webroot.resolve(strict=True), args.tag)
