"""
Update cheias-scrollytelling.qgz with newly generated geodata layers.
Run in QGIS Python Console:
  exec(open('/home/nls/Documents/dev/cheias-pt/scripts/update-qgis-project.py').read())
"""
from qgis.core import (QgsProject, QgsVectorLayer, QgsRasterLayer,
                        QgsLayerTreeGroup, QgsLayerTreeLayer)
import os, urllib.parse

project = QgsProject.instance()
root = project.layerTreeRoot()
DATA = "/home/nls/Documents/dev/cheias-pt/data"
ASSETS = "/home/nls/Documents/dev/cheias-pt/assets"
R2 = "https://pub-abad2527698d4bbab82318691c9b07a1.r2.dev"
TITILER = "https://titiler.cheias.pt"
Q = f"{DATA}/qgis"

# ── Helpers ──

def grp(name):
    for g in root.children():
        if isinstance(g, QgsLayerTreeGroup) and g.name() == name:
            return g
    return None

def has_layer(gname, lname):
    """Check if a layer with this name already exists in the group."""
    g = grp(gname)
    if not g:
        return False
    for child in g.children():
        if isinstance(child, QgsLayerTreeLayer) and child.layer().name() == lname:
            return True
    return False

def vec(path, name, gname, vis=True):
    if has_layer(gname, name):
        print(f"  · {name} (exists)")
        return
    g = grp(gname)
    if not g:
        print(f"  ✗ No group: {gname}")
        return
    lyr = QgsVectorLayer(path, name, "ogr")
    if not lyr.isValid():
        print(f"  ✗ Invalid: {name}")
        return
    project.addMapLayer(lyr, False)
    g.insertLayer(0, lyr).setItemVisibilityChecked(vis)
    print(f"  ✓ {name} ({lyr.featureCount()}f)")

def ras(path, name, gname, vis=True):
    if has_layer(gname, name):
        print(f"  · {name} (exists)")
        return
    g = grp(gname)
    if not g:
        print(f"  ✗ No group: {gname}")
        return
    lyr = QgsRasterLayer(path, name, "gdal")
    if not lyr.isValid():
        print(f"  ✗ Invalid: {name}")
        return
    project.addMapLayer(lyr, False)
    g.addLayer(lyr).setItemVisibilityChecked(vis)
    print(f"  ✓ {name}")

def xyz(cog_r2, name, gname, cmap="blues", rsc="0.2,0.5", vis=True):
    if has_layer(gname, name):
        print(f"  · {name} (exists)")
        return
    g = grp(gname)
    if not g:
        print(f"  ✗ No group: {gname}")
        return
    enc = urllib.parse.quote(f"{R2}/{cog_r2}", safe='')
    turl = (f"{TITILER}/cog/tiles/WebMercatorQuad/{{z}}/{{x}}/{{y}}.png"
            f"?url={enc}&colormap_name={cmap}&rescale={rsc}")
    lyr = QgsRasterLayer(f"type=xyz&url={turl}&zmin=4&zmax=12", name, "wms")
    if not lyr.isValid():
        print(f"  ✗ {name} (titiler)")
        return
    project.addMapLayer(lyr, False)
    g.addLayer(lyr).setItemVisibilityChecked(vis)
    print(f"  ✓ {name} ⚡titiler")

# ═══════════════════════════════════════════════════
# Ch2 — Atlantic Engine: IVT point + raster
# Design: SST anomalies + atmospheric river tracks
# ═══════════════════════════════════════════════════
print("\n── Ch2 — Atlantic Engine (adding IVT) ──")
CH2 = "Ch2 — Atlantic Engine (SST + IVT)"
vec(f"{Q}/ivt-peak-storm.geojson", "IVT Peak Storm (1102 pts)", CH2)
xyz("cog/ivt/ivt-peak-2026-02-10.tif", "IVT Peak Feb10 COG", CH2,
    cmap="reds", rsc="0,500", vis=True)

# ═══════════════════════════════════════════════════
# Ch3 — Sponge Fills: SM peak inspection points
# ═══════════════════════════════════════════════════
print("\n── Ch3 — Sponge Fills (SM peak points) ──")
CH3 = "Ch3 — Sponge Fills (Soil Moisture)"
vec(f"{Q}/soil-moisture-peak-points.geojson", "SM Peak Jan31 points (256)", CH3, vis=False)

# ═══════════════════════════════════════════════════
# Ch4 — Storms: storm total accumulation
# ═══════════════════════════════════════════════════
print("\n── Ch4 — Storms (storm total) ──")
CH4 = "Ch4 — The Storms (Precipitation)"
xyz("cog/precipitation/storm-total.tif", "Precip Storm Total", CH4,
    cmap="ylorrd", rsc="0,400", vis=False)
ras(f"{DATA}/cog/precipitation/storm-total.tif", "Storm Total (local COG)", CH4, vis=False)

# ═══════════════════════════════════════════════════
# Ch5 — Rivers Rise: river polylines + discharge stations
# Design: river lines + discharge hydrographs + basin precondition fill
# ═══════════════════════════════════════════════════
print("\n── Ch5 — Rivers Rise (rivers + stations) ──")
CH5 = "Ch5 — Rivers Rise (Discharge)"
vec(f"{Q}/rivers-portugal.geojson", "Rivers Portugal (264 seg)", CH5)
vec(f"{Q}/discharge-stations.geojson", "Discharge Stations (11)", CH5)

# ═══════════════════════════════════════════════════
# Ch6a-c — Human Cost: add rivers for context
# Design: flood extent + consequence markers + rivers
# ═══════════════════════════════════════════════════
print("\n── Ch6a-c — Adding rivers ──")
vec(f"{Q}/rivers-portugal.geojson", "Rivers (Sado)", "Ch6a — Alcácer do Sal")
vec(f"{Q}/rivers-portugal.geojson", "Rivers (Mondego)", "Ch6b — Coimbra / Mondego")
vec(f"{Q}/rivers-portugal.geojson", "Rivers (context)", "Ch6c — A1 Collapse")

# ═══════════════════════════════════════════════════
# Ch7 — Full Picture (Climax): precondition basins + peak grid
# Design: ALL flood extent + ALL consequences + precondition at peak
# ═══════════════════════════════════════════════════
print("\n── Ch7 — Full Picture (precondition data) ──")
CH7 = "Ch7 — Full Picture (Climax)"
vec(f"{Q}/precondition-basins.geojson", "Precondition Basins (scored)", CH7)
vec(f"{Q}/precondition-peak-points.geojson", "Precondition Peak Grid (256)", CH7, vis=False)
xyz("cog/precondition/2026-02-05.tif", "Precondition Peak Feb05 COG", CH7,
    cmap="rdylgn_r", rsc="0,30", vis=False)
vec(f"{Q}/rivers-portugal.geojson", "Rivers (context)", CH7, vis=False)

# ═══════════════════════════════════════════════════
# Ch8 — Precondition Index: full methodology data
# Design: basins colored by precondition, temporal sequence
# ═══════════════════════════════════════════════════
print("\n── Ch8 — Precondition Index ──")
CH8 = "Ch8 — Precondition Index"
vec(f"{Q}/precondition-basins.geojson", "Precondition Basins (scored)", CH8)
vec(f"{Q}/precondition-peak-points.geojson", "Precondition Peak Grid", CH8, vis=False)
# Temporal sequence of precondition COGs
for date, label in [
    ("2025-12-01", "Dec01 baseline"),
    ("2026-01-15", "Jan15 building"),
    ("2026-01-28", "Jan28 pre-Kristin"),
    ("2026-01-31", "Jan31 post-Kristin"),
    ("2026-02-05", "Feb05 PEAK"),
    ("2026-02-10", "Feb10 post-Leonardo"),
]:
    xyz(f"cog/precondition/{date}.tif", f"Precon {label}", CH8,
        cmap="rdylgn_r", rsc="0,30", vis=(date == "2026-02-05"))

# ═══════════════════════════════════════════════════
# Ch9 — Explore Mode: all new layers as toggleable
# ═══════════════════════════════════════════════════
print("\n── Ch9 — Explore (all new layers) ──")
CH9 = "Ch9 — Explore Mode"
vec(f"{Q}/rivers-portugal.geojson", "Rivers (toggleable)", CH9, vis=False)
vec(f"{Q}/discharge-stations.geojson", "Discharge Stations (toggleable)", CH9, vis=False)
vec(f"{Q}/precondition-basins.geojson", "Precondition Basins (toggleable)", CH9, vis=False)
vec(f"{Q}/ivt-peak-storm.geojson", "IVT Peak (toggleable)", CH9, vis=False)
xyz("cog/precondition/2026-02-05.tif", "Precondition Peak (toggleable)", CH9,
    cmap="rdylgn_r", rsc="0,30", vis=False)
xyz("cog/precipitation/storm-total.tif", "Storm Total Precip (toggleable)", CH9,
    cmap="ylorrd", rsc="0,400", vis=False)

# ═══════════════════════════════════════════════════
# SAVE + REPORT
# ═══════════════════════════════════════════════════
project.write()

print(f"\n{'═'*55}")
print(f"✓ Project saved: {project.fileName()}")
print(f"✓ Total layers: {len(project.mapLayers())}")
print(f"{'═'*55}")
for g in root.children():
    if isinstance(g, QgsLayerTreeGroup):
        def count_layers(node):
            c = 0
            for child in node.children():
                if isinstance(child, QgsLayerTreeLayer):
                    c += 1
                elif isinstance(child, QgsLayerTreeGroup):
                    c += count_layers(child)
            return c
        n = count_layers(g)
        print(f"  {g.name()}: {n} layers")
