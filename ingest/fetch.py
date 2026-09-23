import hashlib
import json
import os
import subprocess

MANIFEST = "data/manifest.json"
CHUNK = 4 * 1024 * 1024


def sha1_of(path):
    h = hashlib.sha1()
    with open(path, "rb") as f:
        while chunk := f.read(CHUNK):
            h.update(chunk)
    return h.hexdigest()


def download(url, path):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    subprocess.run(["curl", "-L", "-C", "-", "-o", path, url], check=True)


def verify(name, src):
    """Refuse to continue unless the archive on disk is the one the manifest names."""
    actual_size = os.path.getsize(src["path"])
    if actual_size != src["bytes"]:
        raise SystemExit(f"{name}: size mismatch, expected {src['bytes']} got {actual_size}")

    actual_sha1 = sha1_of(src["path"])
    if actual_sha1 != src["sha1"]:
        raise SystemExit(
            f"{name}: sha1 mismatch\n  expected {src['sha1']}\n  got      {actual_sha1}"
        )


def needs_extract(src):
    """True if any file we depend on is missing or the wrong size.

    The archive's sha1 says nothing about the files extracted from it - those
    are separate files on disk that can be deleted or truncated afterwards.
    Checking their sizes costs milliseconds; extracting costs a minute, so the
    expensive step sits behind the cheap test.
    """
    for filename, expected_bytes in src["extracted_files"].items():
        path = os.path.join(src["extract_to"], filename)
        if not os.path.exists(path) or os.path.getsize(path) != expected_bytes:
            return True
    return False


def extract(src):
    # 7z stores a CRC32 for every file and checks it while writing, so a clean
    # exit means the extracted bytes are correct. check=True turns any failure
    # into a crash instead of a silently bad load.
    os.makedirs(src["extract_to"], exist_ok=True)
    subprocess.run(["7z", "x", src["path"], f"-o{src['extract_to']}", "-y"], check=True)


def main():
    with open(MANIFEST) as f:
        manifest = json.load(f)

    for name, src in manifest["sources"].items():
        if not os.path.exists(src["path"]):
            print(f"{name}: downloading")
            download(src["url"], src["path"])

        print(f"{name}: verifying archive")
        verify(name, src)

        if needs_extract(src):
            print(f"{name}: extracting")
            extract(src)
        else:
            print(f"{name}: extracted files already present and correct size")

    print("all sources ok")


if __name__ == "__main__":
    main()
