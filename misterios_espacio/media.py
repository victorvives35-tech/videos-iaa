# -*- coding: utf-8 -*-
"""Descarga imágenes y vídeos de la NASA Image and Video Library (images.nasa.gov).
Guarda metadatos (título, centro, autor) para los créditos de la descripción."""
import json, os, re, sys, time, urllib.parse, urllib.request
from concurrent.futures import ThreadPoolExecutor

WORK = os.environ["WORK"]
MED = os.path.join(WORK, "media"); os.makedirs(MED, exist_ok=True)
API = "https://images-api.nasa.gov/search?"

IMG_Q = {
    "galaxy": ["spiral galaxy Hubble", "galaxy Webb"], "nebula": ["nebula Webb", "nebula Hubble"],
    "webb": ["Webb telescope image"], "deepfield": ["deep field Webb", "Hubble ultra deep field"],
    "earth": ["Earth from space station"], "blackhole": ["black hole illustration"], "saturn": ["Saturn Cassini"],
    "jupiter": ["Jupiter Juno"], "galaxy_cluster": ["galaxy cluster Hubble", "Bullet Cluster"],
    "lensing": ["gravitational lensing"], "euclid": ["Euclid mission"], "supernova": ["supernova remnant"],
    "radio": ["radio telescope antenna"], "magnetar": ["magnetar"], "neutron_star": ["neutron star"],
    "gravitational_waves": ["gravitational waves"], "m87": ["M87 black hole"], "sgra": ["Sagittarius A*"],
    "hubble": ["Hubble Space Telescope orbit"], "cepheid": ["Cepheid variable"], "planck_cmb": ["cosmic microwave background"],
    "cmb": ["WMAP"], "bigbang": ["Big Bang"], "df2": ["NGC 1052-DF2", "galaxy lacking dark matter"],
    "dwarf_galaxy": ["dwarf galaxy Hubble"], "europa": ["Europa moon surface", "Europa Galileo"],
    "europa_clipper": ["Europa Clipper"], "ice": ["Europa ice"], "titan": ["Titan Cassini", "Titan lakes"],
    "cassini": ["Cassini spacecraft"], "huygens": ["Huygens probe Titan"], "dragonfly": ["Dragonfly Titan"],
    "early_galaxy": ["early galaxies Webb"], "jades": ["JADES Webb"], "expansion": ["expanding universe"],
    "rotation": ["Vera Rubin"],
}
VID_Q = {
    "blackhole": ["black hole visualization", "black hole simulation"], "galaxy": ["galaxy zoom", "galaxy animation"],
    "webb": ["Webb zoom", "Webb animation"], "deepfield": ["deep field fly-through"], "earth": ["Earth from space"],
    "europa": ["Europa animation", "Europa Clipper"], "titan": ["Titan animation", "Dragonfly"],
    "saturn": ["Saturn Cassini animation"], "jupiter": ["Juno Jupiter flyby"], "supernova": ["supernova animation"],
    "neutron_star": ["neutron star animation", "magnetar animation"], "gravitational_waves": ["gravitational waves animation"],
    "nebula": ["nebula fly-through", "nebula visualization"], "hubble": ["Hubble telescope animation"],
    "galaxy_cluster": ["dark matter animation", "galaxy cluster animation"], "cmb": ["cosmic microwave background animation"],
}
BAD = re.compile(r"(this week|live|episode|interview|briefing|conference|we asked|podcast|q&a|panel|update|news|town hall|explains)", re.I)


def get(url, tries=3):
    for k in range(tries):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": "doc-maker/1.0"}), timeout=60) as r:
                return r.read()
        except Exception as e:
            if k == tries - 1:
                print("ERR", url[:90], e)
            time.sleep(2)


def search(q, media, n):
    d = get(API + urllib.parse.urlencode({"q": q, "media_type": media, "page_size": max(n * 3, 20)}))
    if not d:
        return []
    items = json.loads(d)["collection"]["items"]
    out = []
    for it in items:
        m = it["data"][0]
        if media == "video" and BAD.search(m.get("title", "")):
            continue
        out.append((m, it["href"]))
        if len(out) >= n:
            break
    return out


def fetch(job):
    theme, media, m, href = job
    nid = re.sub(r"[^A-Za-z0-9_.-]", "_", m["nasa_id"])[:80]
    ext = "jpg" if media == "image" else "mp4"
    dst = os.path.join(MED, media, theme, f"{nid}.{ext}")
    if os.path.exists(dst):
        return dst, m
    os.makedirs(os.path.dirname(dst), exist_ok=True)
    col = get(href.replace(" ", "%20").replace("http://", "https://"))
    if not col:
        return None, m
    files = json.loads(col)
    pref = ["~large.jpg", "~medium.jpg", "~orig.jpg"] if media == "image" else ["~large.mp4", "~medium.mp4", "~orig.mp4", "~mobile.mp4"]
    url = None
    for p in pref:
        for f in files:
            if f.endswith(p):
                url = f; break
        if url: break
    if not url:
        return None, m
    data = get(url.replace(" ", "%20").replace("http://", "https://"))
    if not data:
        return None, m
    open(dst, "wb").write(data)
    return dst, m


jobs = []
for theme, qs in IMG_Q.items():
    for q in qs:
        for m, h in search(q, "image", 6):
            jobs.append((theme, "image", m, h))
for theme, qs in VID_Q.items():
    for q in qs:
        for m, h in search(q, "video", 3):
            jobs.append((theme, "video", m, h))
print(len(jobs), "descargas", flush=True)
meta = {}
with ThreadPoolExecutor(6) as ex:
    for dst, m in ex.map(fetch, jobs):
        if dst:
            meta[dst] = {"title": m.get("title"), "nasa_id": m.get("nasa_id"), "center": m.get("center"),
                         "creator": m.get("secondary_creator") or m.get("photographer") or "", "date": m.get("date_created", "")[:10]}
json.dump(meta, open(os.path.join(WORK, "media_meta.json"), "w"), indent=1, ensure_ascii=False)
print("OK", len(meta))
