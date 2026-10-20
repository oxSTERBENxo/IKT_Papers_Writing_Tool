"""List or extract selected members of a remote zip using HTTP Range requests,
so only the central directory and the chosen members are transferred.

Usage:
  python -I remote_zip.py list <url>
  python -I remote_zip.py get <url> <out_dir> <member> [<member> ...] [--max-mb N]
"""
import struct
import sys
import urllib.request
import zlib
from pathlib import Path

UA = {"User-Agent": "sra-audit/1.0"}


def fetch(url, start, end):
    req = urllib.request.Request(url, headers={**UA, "Range": f"bytes={start}-{end}"})
    with urllib.request.urlopen(req, timeout=120) as r:
        if r.status != 206:
            raise SystemExit(f"server ignored Range (status {r.status}); refusing full download")
        total = int(r.headers["Content-Range"].split("/")[-1])
        return r.read(), total


def central_directory(url):
    tail, total = fetch(url, 0, 0)
    tail, _ = fetch(url, max(0, total - 70000), total - 1)
    i = tail.rfind(b"PK\x05\x06")
    if i < 0:
        raise SystemExit("end of central directory not found")
    n, size, offset = struct.unpack("<HII", tail[i + 10:i + 20])
    if offset == 0xFFFFFFFF:  # zip64
        j = tail.rfind(b"PK\x06\x06")
        size, offset = struct.unpack("<QQ", tail[j + 40:j + 56])
    cd, _ = fetch(url, offset, offset + size - 1)
    members, p = [], 0
    while cd[p:p + 4] == b"PK\x01\x02":
        method, = struct.unpack("<H", cd[p + 10:p + 12])
        csize, usize = struct.unpack("<II", cd[p + 20:p + 28])
        nlen, elen, clen = struct.unpack("<HHH", cd[p + 28:p + 34])
        loff, = struct.unpack("<I", cd[p + 42:p + 46])
        name = cd[p + 46:p + 46 + nlen].decode("utf-8", "replace")
        extra = cd[p + 46 + nlen:p + 46 + nlen + elen]
        q = 0
        while q + 4 <= len(extra):  # zip64 extra field
            hid, hlen = struct.unpack("<HH", extra[q:q + 4])
            if hid == 1:
                vals, r = [], q + 4
                for flag in (usize, csize, loff):
                    if flag == 0xFFFFFFFF:
                        vals.append(struct.unpack("<Q", extra[r:r + 8])[0]); r += 8
                    else:
                        vals.append(flag)
                usize, csize, loff = vals
            q += 4 + hlen
        members.append({"name": name, "method": method, "csize": csize, "usize": usize, "offset": loff})
        p += 46 + nlen + elen + clen
    return total, members


def extract(url, m):
    head, _ = fetch(url, m["offset"], m["offset"] + 29)
    nlen, elen = struct.unpack("<HH", head[26:30])
    start = m["offset"] + 30 + nlen + elen
    data, _ = fetch(url, start, start + m["csize"] - 1)
    if m["method"] == 0:
        return data
    if m["method"] == 8:
        return zlib.decompress(data, -15)
    raise SystemExit(f"unsupported compression {m['method']}")


if __name__ == "__main__":
    cmd, url = sys.argv[1], sys.argv[2]
    total, members = central_directory(url)
    if cmd == "list":
        print(f"archive size {total / 1e6:.1f} MB")
        for m in members:
            print(f"{m['csize'] / 1e6:10.2f} MB compressed  {m['usize'] / 1e6:10.2f} MB  {m['name']}")
    else:
        out = Path(sys.argv[3]); out.mkdir(parents=True, exist_ok=True)
        args = sys.argv[4:]
        max_mb = 50.0
        if "--max-mb" in args:
            k = args.index("--max-mb"); max_mb = float(args[k + 1]); args = args[:k] + args[k + 2:]
        by_name = {m["name"]: m for m in members}
        for name in args:
            m = by_name.get(name)
            if not m:
                print(f"missing: {name}"); continue
            if m["csize"] / 1e6 > max_mb:
                print(f"skipped {name}: {m['csize'] / 1e6:.1f} MB exceeds --max-mb {max_mb}"); continue
            target = out / Path(name).name
            target.write_bytes(extract(url, m))
            print(f"wrote {target} ({target.stat().st_size / 1e6:.2f} MB)")
