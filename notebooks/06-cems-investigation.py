"""
06-cems-investigation.py
========================
Investigates Copernicus EMS Rapid Mapping activations for Portugal 2026 floods.

EMSR861 — Storm Kristin (activated 2026-01-28)
EMSR864 — Storm Leonardo (activated 2026-02-03)

Queries the CEMS Rapid Mapping API to enumerate AOIs and products.
Outputs findings to data/flood-extent/README.md (already written manually).

Run: python notebooks/06-cems-investigation.py
"""

import json
import urllib.request
from pathlib import Path

API_BASE = "https://rapidmapping.emergency.copernicus.eu/backend/dashboard-api/public-activations/"
ACTIVATIONS = ["EMSR861", "EMSR864"]

# Portugal-relevant AOI keywords
PT_KEYWORDS = [
    "coimbra", "castelo branco", "lisboa", "santarém", "salvaterra",
    "ermidas", "sado", "moinhos", "tejo", "mondego", "portugal",
    "alcácer", "leiria", "aveiro",
]


def fetch_activation(code: str) -> dict:
    """Fetch activation details from CEMS Rapid Mapping API."""
    url = f"{API_BASE}?code={code}"
    print(f"Fetching {url}")
    try:
        req = urllib.request.Request(url, headers={"Accept": "application/json"})
        with urllib.request.urlopen(req, timeout=30) as resp:
            data = json.loads(resp.read().decode())
            # API returns a list; take first result
            if isinstance(data, list):
                return data[0] if data else {}
            if isinstance(data, dict) and "results" in data:
                return data["results"][0] if data["results"] else {}
            return data
    except Exception as e:
        print(f"  Error fetching {code}: {e}")
        return {}


def is_portugal_aoi(aoi: dict) -> bool:
    """Check if an AOI is relevant to Portugal."""
    name = (aoi.get("name", "") or "").lower()
    description = (aoi.get("description", "") or "").lower()
    text = f"{name} {description}"
    return any(kw in text for kw in PT_KEYWORDS)


def print_activation_summary(data: dict):
    """Print a structured summary of an activation."""
    code = data.get("code", "???")
    name = data.get("name", "")
    n_aois = data.get("n_aois", 0)
    n_products = data.get("n_products", 0)
    activated = data.get("activationTime", "")
    closed = data.get("closed", None)

    print(f"\n{'='*60}")
    print(f"Activation: {code}")
    print(f"Name:       {name}")
    print(f"Activated:  {activated}")
    print(f"Closed:     {closed}")
    print(f"AOIs:       {n_aois}")
    print(f"Products:   {n_products}")

    # Extract AOIs if available
    aois = data.get("aois", [])
    if not aois:
        print("  (AOI details not available in summary endpoint)")
        return

    print(f"\nAOIs ({len(aois)} total):")
    for aoi in aois:
        aoi_num = aoi.get("number", "?")
        aoi_name = aoi.get("name", "unnamed")
        pt_flag = " [PORTUGAL]" if is_portugal_aoi(aoi) else ""
        products = aoi.get("products", [])
        print(f"  AOI{aoi_num:>2}: {aoi_name}{pt_flag} ({len(products)} products)")

        for prod in products:
            prod_type = prod.get("type", "???")
            monitoring = prod.get("monitoringNumber", "")
            download = prod.get("downloadPath", "")
            status = prod.get("status", "")
            satellite = prod.get("satelliteName", "")

            mon_label = f"_MONIT{monitoring:02d}" if monitoring else ""
            dl_label = f" -> {download}" if download else " (no download)"
            print(f"    {prod_type}{mon_label} [{satellite}] status={status}{dl_label}")


def main():
    print("CEMS Rapid Mapping Investigation")
    print("Portugal Floods Jan-Feb 2026")
    print(f"Activations: {', '.join(ACTIVATIONS)}")

    for code in ACTIVATIONS:
        data = fetch_activation(code)
        if data:
            print_activation_summary(data)
        else:
            print(f"\nNo data returned for {code}")

    # Summary for cheias.pt
    print(f"\n{'='*60}")
    print("SUMMARY FOR cheias.pt")
    print("="*60)
    print("""
Key findings:
1. EMSR861 (Kristin): 27 AOIs, mostly Spain. Portugal AOIs: Coimbra (AOI05), Castelo Branco (AOI06).
2. EMSR864 (Leonardo): 18 AOIs, focused on Portugal. Key AOIs:
   - AOI01 Ermidas Sado: 2,667 ha flooded, 6k affected
   - AOI02 Rio de Moinhos: 7,127 ha flooded, 8.5k affected
   - AOI03 Salvaterra de Magos: 64,198 ha flooded, 410k affected

Data format: ZIP containing GDB, GeoJSON, TIFF, PDF
Download: Free, no registration, direct URLs via API
API: https://rapidmapping.emergency.copernicus.eu/backend/dashboard-api/public-activations/?code=EMSR864

Priority downloads for cheias.pt:
- EMSR864 AOI03 (Tejo/Salvaterra): largest flood extent
- EMSR864 AOI01 (Sado/Ermidas): Sado basin flooding
- EMSR864 AOI02 (Rio de Moinhos): additional coverage
- EMSR861 AOI05 (Coimbra): Mondego basin, Kristin damage

See data/flood-extent/README.md for full details and wget commands.
""")


if __name__ == "__main__":
    main()
