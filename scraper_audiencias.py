"""
Scraper diario de audiencias TV (España) a partir de FormulaTV.

Uso:
    python scraper_audiencias.py                       # scrapea el día de ayer
    python scraper_audiencias.py 2026-07-01 2026-07-17  # scrapea un rango de fechas

Guarda un JSON por día en data/AAAA-MM-DD.json y reconstruye data/history.json
(agregado de todos los días, que es lo que lee el dashboard).

IMPORTANTE:
- No probado en vivo contra formulatv.com (sandbox de desarrollo sin acceso a
  ese dominio). Antes de fiarte del todo, abre "ver código fuente" sobre
  https://www.formulatv.com/audiencias/2026-07-17/ y confirma que los nombres
  de archivo de los logos (logo_la1.svg, logo_antena3.svg...) y el formato de
  porcentaje ("14,2%") coinciden con el patrón de abajo (PAIR_RE). Si la web
  cambia de plantilla algún día, solo hay que tocar esa expresión regular y el
  diccionario SLUG_TO_NAME.
- Solo se extraen datos numéricos (cadena + cuota), nunca texto editorial.
- Pausa entre peticiones para no saturar el servidor.
"""

import re
import json
import time
import sys
from datetime import date, timedelta
from pathlib import Path

import requests

BASE_URL = "https://www.formulatv.com/audiencias/{date}/"
HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; AudienciasResearchBot/1.0; +academic use)"}
DATA_DIR = Path(__file__).parent / "data"

PAIR_RE = re.compile(
    r"logo_([a-z0-9\-]+)\.svg.*?(\d{1,2},\d)%",
    re.IGNORECASE | re.DOTALL,
)

SLUG_TO_NAME = {
    "la1": "La 1", "antena3": "Antena 3", "telecinco": "Telecinco",
    "cuatro": "Cuatro", "lasexta": "laSexta", "la2": "La 2",
    "fdf": "FDF", "nova": "Nova", "13tv": "Trece", "energy": "Energy",
    "neox": "Neox", "atreseries": "Atreseries", "discoverymax": "DMAX",
    "dkiss": "DKiss", "bemadtv": "BeMad", "canal24horas": "Canal 24 Horas",
    "mega-espana": "Mega", "veo7": "Veo7", "boing": "Boing", "ten": "Ten",
    "divinity": "Divinity", "clan": "Clan TVE", "teledeporte": "Teledeporte",
    "real-madrid-tv": "Real Madrid TV",
}


def fetch_day(day: date) -> list[dict]:
    url = BASE_URL.format(date=day.isoformat())
    resp = requests.get(url, headers=HEADERS, timeout=15)
    resp.raise_for_status()
    html = resp.text

    cutoff = html.find("Calendario")
    if cutoff != -1:
        html = html[:cutoff]

    results = []
    seen = set()
    for slug, pct in PAIR_RE.findall(html):
        slug = slug.lower()
        if slug in seen:
            continue
        seen.add(slug)
        name = SLUG_TO_NAME.get(slug, slug.replace("-", " ").title())
        share = float(pct.replace(",", "."))
        results.append({"cadena": name, "cuota": share})

    return results


FRANJAS_URL = "https://www.formulatv.com/audiencias/{date}/franjas/"

# Claves del chartData embebido en la página de franjas -> nombre legible de cadena/grupo
FRANJA_KEYS = {
    "CuotaLa1": "La 1",
    "CuotaLa2": "La 2",
    "CuotaA3": "Antena 3",
    "CuotaT5": "Telecinco",
    "CuotaCuatro": "Cuatro",
    "CuotaLa6": "laSexta",
    "AutPub": "Autonómicas públicas",
    "AutPriv": "Autonómicas privadas",
    "TemTDT": "Temáticas TDT",
    "TemPago": "Temáticas de pago",
}

CHARTDATA_RE = re.compile(r"var\s+chartData\s*=\s*(\[[\s\S]*?\]);")


def fetch_franjas(day: date) -> list[dict]:
    """Descarga el desglose de audiencia por franja horaria (Madrugada, Mañana, etc.)."""
    url = FRANJAS_URL.format(date=day.isoformat())
    resp = requests.get(url, headers=HEADERS, timeout=15)
    resp.raise_for_status()
    html = resp.text

    match = CHARTDATA_RE.search(html)
    if not match:
        return []

    raw = json.loads(match.group(1))
    franjas = []
    for row in raw:
        cuotas = {}
        for key, name in FRANJA_KEYS.items():
            val = row.get(key, "")
            if val not in ("", None):
                cuotas[name] = float(val)
        franjas.append({"franja": row.get("hora", ""), "cuotas": cuotas})
    return franjas


def save_franjas(day: date, franjas: list[dict]) -> None:
    if not franjas:
        return
    dir_path = DATA_DIR / "franjas"
    dir_path.mkdir(parents=True, exist_ok=True)
    path = dir_path / f"{day.isoformat()}.json"
    payload = {"fecha": day.isoformat(), "franjas": franjas}
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def save_day(day: date, data: list[dict]) -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    path = DATA_DIR / f"{day.isoformat()}.json"
    payload = {"fecha": day.isoformat(), "canales": data}
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def rebuild_history() -> None:
    """Recombina todos los JSON diarios en un único history.json para el dashboard."""
    days = []
    for f in sorted(DATA_DIR.glob("????-??-??.json")):
        try:
            days.append(json.loads(f.read_text(encoding="utf-8")))
        except Exception:
            continue
    history_path = DATA_DIR / "history.json"
    history_path.write_text(json.dumps(days, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"history.json reconstruido con {len(days)} días")

    franjas_dir = DATA_DIR / "franjas"
    if franjas_dir.exists():
        franja_days = []
        for f in sorted(franjas_dir.glob("????-??-??.json")):
            try:
                franja_days.append(json.loads(f.read_text(encoding="utf-8")))
            except Exception:
                continue
        (DATA_DIR / "history-franjas.json").write_text(
            json.dumps(franja_days, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        print(f"history-franjas.json reconstruido con {len(franja_days)} días")


def backfill(start: date, end: date) -> None:
    d = start
    while d <= end:
        try:
            data = fetch_day(d)
            if data:
                save_day(d, data)
                print(f"{d}: {len(data)} canales guardados")
            else:
                print(f"{d}: sin datos (¿estructura de página distinta?)")
        except Exception as e:
            print(f"{d}: error (cadenas) -> {e}")

        time.sleep(1)

        try:
            franjas = fetch_franjas(d)
            if franjas:
                save_franjas(d, franjas)
                print(f"{d}: franjas guardadas")
            else:
                print(f"{d}: sin datos de franjas")
        except Exception as e:
            print(f"{d}: error (franjas) -> {e}")

        time.sleep(1.5)
        d += timedelta(days=1)
    rebuild_history()


if __name__ == "__main__":
    if len(sys.argv) == 3:
        start = date.fromisoformat(sys.argv[1])
        end = date.fromisoformat(sys.argv[2])
    else:
        end = date.today() - timedelta(days=1)
        start = end

    backfill(start, end)
