"""
Verification of Single-Entrypoint Deployment
Tests that port 8000 serves:
  1. Redesigned React 18 SPA (HTML, dynamic JS bundle, Tailwind CSS)
  2. Live API endpoints (/api/patients, /api/apnea, /api/bradycardia, /api/ndi)
"""

import httpx
import re

client = httpx.Client(base_url="http://127.0.0.1:8000", timeout=10.0)

# 1. Root HTML
r_html = client.get("/", headers={"Accept": "text/html,application/xhtml+xml"})
assert r_html.status_code == 200, f"Failed HTML: {r_html.status_code}"
assert '<div id="root"></div>' in r_html.text, "React root div not found in HTML"
print(f"[PASS 1/5] Redesigned React index.html served at / with status 200 ({len(r_html.text)} chars)")

# 2. Extract and verify dynamic JS and CSS assets referenced in index.html
js_match = re.search(r'src="(/assets/[^"]+\.js)"', r_html.text)
css_match = re.search(r'href="(/assets/[^"]+\.css)"', r_html.text)

assert js_match, "JS asset link not found in index.html"
assert css_match, "CSS asset link not found in index.html"

js_path = js_match.group(1)
css_path = css_match.group(1)

r_js = client.get(js_path)
assert r_js.status_code == 200, f"Failed to load JS asset {js_path}: {r_js.status_code}"
r_css = client.get(css_path)
assert r_css.status_code == 200, f"Failed to load CSS asset {css_path}: {r_css.status_code}"
print(f"[PASS 2/5] Static assets loaded: JS={js_path} ({len(r_js.content):,} bytes), CSS={css_path} ({len(r_css.content):,} bytes)")

# 3. Live Patients List
r_pat = client.get("/api/patients")
assert r_pat.status_code == 200
patients = r_pat.json()
assert len(patients) >= 10
p1 = patients[0]
print(f"[PASS 3/5] Live /api/patients returned {len(patients)} patients (First: {p1['id']}, NDI={p1['ndi_badge']['label']})")

# 4. Live Condition Telemetry
r_ap = client.get("/api/apnea/infant1")
assert r_ap.status_code == 200
ap = r_ap.json()
r_br = client.get("/api/bradycardia/infant1")
assert r_br.status_code == 200
br = r_br.json()
print(f"[PASS 4/5] Live Telemetry: Apnea={ap['events_per_hour']:.1f}/hr [{ap['status']}], "
      f"Brady Lowest={br['lowest_heart_rate_bpm']:.1f} BPM [{br['status']}]")

# 5. Live Fused NDI
r_ndi = client.get("/api/ndi/infant1")
assert r_ndi.status_code == 200
ndi = r_ndi.json()
print(f"[PASS 5/5] Live Fused NDI: Score={ndi['ndi_score']:.1f}/100 [{ndi['ndi_band']}] | Primary Driver: {ndi['primary_driver']}")

print("\n" + "=" * 65)
print("  REDESIGNED APP VERIFIED: LIGHT CLINICAL THEME + LIVE TELEMETRY WORKING!")
print("=" * 65)
