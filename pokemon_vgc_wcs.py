import json
import html
import webbrowser
from pathlib import Path
from collections import defaultdict

# Scoring system
placement_points = {
    (1, 1): 350,
    (2, 2): 325,
    (3, 4): 300,
    (5, 8): 280,
    (9, 16): 200,
    (17, 32): 160,
    (33, 64): 120,
    (65, 128): 80,
    (129, 256): 60,
    (257, 512): 45,
    (513, 1024): 22
}


def calculate_points(placing):
    try:
        placing = int(placing)
    except (ValueError, TypeError):
        return 0

    for (minimum, maximum), points in placement_points.items():
        if minimum <= placing <= maximum:
            return points

    return 0


def esc(value):
    return html.escape(str(value), quote=True)


def main():
    script_folder = Path(__file__).resolve().parent
    data_folder = script_folder / "player_placings"
    data_folder.mkdir(exist_ok=True)
    json_files = sorted(data_folder.glob("*.json"))

    if not json_files:
        raise SystemExit(
            f"No JSON files found in {data_folder}. Put tournament JSON files "
            "in the player_placings folder and run this script again."
        )

    # players[name][source filename] = placing
    players = defaultdict(dict)

    for json_file in json_files:
        print(f"Reading {json_file.name}...")
        try:
            with json_file.open("r", encoding="utf-8-sig") as file:
                data = json.load(file)

            if isinstance(data, dict):
                data = data.get("players", [data])
            if not isinstance(data, list):
                print(f"Skipping {json_file.name}: unexpected JSON structure.")
                continue

            accepted = 0
            for entry in data:
                if not isinstance(entry, dict):
                    continue
                name = entry.get("name")
                placing = entry.get("placing")
                if name is None or placing is None:
                    continue
                name = str(name).strip()
                if name:
                    players[name][json_file.name] = placing
                    accepted += 1

            if accepted == 0:
                print(
                    f"Warning: no records with both 'name' and 'placing' "
                    f"were found in {json_file.name}."
                )
        except (json.JSONDecodeError, OSError) as error:
            print(f"Could not read {json_file.name}: {error}")

    if not players:
        raise SystemExit(
            "No usable player records found. Each player entry must contain "
            "both 'name' and 'placing'."
        )

    player_rows = []
    for name, results in players.items():
        event_results = []
        total = 0
        for json_file in json_files:
            placing = results.get(json_file.name)
            points = calculate_points(placing) if placing is not None else 0
            event_results.append((placing, points))
            total += points
        player_rows.append({
            "name": name, "results": event_results, "total": total,
        })

    player_rows.sort(key=lambda player: (-player["total"], player["name"].casefold()))

    event_headers = "".join(
        f'<th colspan="2">{esc(file.stem)}</th>' for file in json_files
    )
    sub_headers = "".join(
        "<th>Place</th><th>Points</th>" for _ in json_files
    )

    table_rows = []
    for rank, player in enumerate(player_rows, start=1):
        cells = [
            f'<td class="rank">{rank}</td>',
            f'<td class="player-name">{esc(player["name"])}</td>',
        ]
        for placing, points in player["results"]:
            place_text = "—" if placing is None else esc(placing)
            points_text = "—" if placing is None else str(points)
            cells.extend([
                f'<td class="number">{place_text}</td>',
                f'<td class="number">{points_text}</td>',
            ])
        cells.append(f'<td class="number total">{player["total"]}</td>')
        table_rows.append("<tr>" + "".join(cells) + "</tr>")

    top_players = player_rows[:10]
    max_points = max((p["total"] for p in top_players), default=0)
    chart_rows = []
    for rank, player in enumerate(top_players, start=1):
        width = player["total"] / max_points * 100 if max_points else 0
        chart_rows.append(
            '<div class="bar-row">'
            f'<div class="bar-label" title="{esc(player["name"])}">'
            f'<span class="bar-rank">{rank}.</span> {esc(player["name"])}</div>'
            '<div class="bar-track">'
            f'<div class="bar" style="width:{width:.2f}%"></div></div>'
            f'<div class="bar-value">{player["total"]}</div></div>'
        )
    event_names = ", ".join(file.stem for file in json_files)
    report = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Pokémon VGC Player Placings</title>
<style>
:root {{ color-scheme: light; --bg:#f4f6fb; --surface:#fff; --text:#1e293b;
--muted:#64748b; --border:#dbe2ee; --accent:#3563d9; }}
* {{ box-sizing:border-box; }}
body {{ margin:0; padding:28px; background:var(--bg); color:var(--text);
font-family:system-ui,-apple-system,"Segoe UI",sans-serif; }}
main {{ max-width:1500px; margin:0 auto; }}
h1 {{ margin:0 0 6px; font-size:clamp(1.6rem,3vw,2.25rem); }}
h2 {{ margin:0 0 16px; font-size:1.2rem; }}
.subtitle {{ margin:0 0 24px; color:var(--muted); }}
.summary {{ display:flex; flex-wrap:wrap; gap:12px; margin-bottom:24px; }}
.metric {{ flex:1 1 160px; background:var(--surface); border:1px solid var(--border);
border-radius:12px; padding:16px 18px; }}
.metric-label {{ color:var(--muted); font-size:.88rem; }}
.metric-value {{ font-size:1.6rem; font-weight:750; margin-top:4px; }}
.panel {{ background:var(--surface); border:1px solid var(--border); border-radius:14px;
padding:20px; margin-bottom:22px; box-shadow:0 2px 8px rgba(20,35,70,.035); }}
.chart {{ display:grid; gap:12px; }}
.bar-row {{ display:grid; grid-template-columns:minmax(120px,260px) minmax(80px,1fr) 56px;
align-items:center; gap:12px; }}
.bar-label {{ overflow:hidden; text-overflow:ellipsis; white-space:nowrap; font-size:.92rem; }}
.bar-rank {{ display:inline-block; min-width:24px; color:var(--muted); }}
.bar-track {{ height:18px; background:#edf1f8; border-radius:5px; overflow:hidden; }}
.bar {{ height:100%; background:var(--accent); border-radius:5px; }}
.bar-value {{ text-align:right; font-weight:700; font-variant-numeric:tabular-nums; }}
.table-tools {{ display:flex; flex-wrap:wrap; gap:12px; justify-content:space-between;
align-items:center; margin-bottom:14px; }}
#search {{ width:min(100%,360px); padding:10px 12px; border:1px solid var(--border);
border-radius:8px; font:inherit; background:white; color:var(--text); }}
.table-wrap {{ overflow:auto; max-height:70vh; border:1px solid var(--border); border-radius:9px; }}
table {{ border-collapse:separate; border-spacing:0; width:100%; font-size:.9rem; white-space:nowrap; }}
th,td {{ padding:10px 12px; border-right:1px solid var(--border); border-bottom:1px solid var(--border); }}
thead th {{ position:sticky; background:#eaf0fc; text-align:center; z-index:2; }}
thead tr:first-child th {{ top:0; }}
thead tr:nth-child(2) th {{ top:41px; background:#f3f6fd; }}
th:first-child,td:first-child {{ position:sticky; left:0; z-index:3; background:#f8faff; }}
thead th:first-child {{ z-index:5; }}
th:last-child,td:last-child {{ border-right:0; }}
tbody tr:last-child td {{ border-bottom:0; }}
tbody tr:nth-child(even) td {{ background:#fafbfe; }}
tbody tr:hover td {{ background:#edf3ff; }}
.rank {{ text-align:right; color:var(--muted); }}
.player-name {{ min-width:210px; font-weight:600; }}
.number {{ text-align:right; font-variant-numeric:tabular-nums; }}
.total {{ font-weight:800; color:#1d48ae; background:#edf3ff !important; }}
.footnote {{ color:var(--muted); font-size:.86rem; margin:12px 0 0; }}
@media(max-width:700px) {{ body {{padding:14px;}} .panel {{padding:14px;}}
.bar-row {{grid-template-columns:minmax(95px,150px) minmax(50px,1fr) 42px;gap:7px;}}
.bar-label {{font-size:.8rem;}} }}
</style>
</head>
<body>
<main>
<h1>Pokémon VGC Player Placings</h1>
<p class="subtitle">Tournament performance comparison · Source files: {esc(event_names)}</p>
<section class="summary">
<div class="metric"><div class="metric-label">Players</div><div class="metric-value">{len(player_rows):,}</div></div>
<div class="metric"><div class="metric-label">Tournaments loaded</div><div class="metric-value">{len(json_files):,}</div></div>
<div class="metric"><div class="metric-label">Highest total score</div><div class="metric-value">{player_rows[0]["total"]:,}</div></div>
</section>
<section class="panel"><h2>Top 10 by total points</h2><div class="chart">{"".join(chart_rows)}</div></section>
<section class="panel">
<h2>Full standings</h2>
<div class="table-tools">
<input id="search" type="search" placeholder="Search player names..." aria-label="Search player names">
<span id="row-count">{len(player_rows):,} players</span>
</div>
<div class="table-wrap">
<table id="standings">
<thead>
<tr><th rowspan="2">Rank</th><th rowspan="2">Player</th>{event_headers}<th rowspan="2">Total points</th></tr>
<tr>{sub_headers}</tr>
</thead>
<tbody>{"".join(table_rows)}</tbody>
</table>
</div>
<p class="footnote">Ranked by total points, highest first. A missing tournament result is shown as — and contributes 0 points.</p>
</section>
</main>
<script>
const search = document.getElementById("search");
const rows = Array.from(document.querySelectorAll("#standings tbody tr"));
const rowCount = document.getElementById("row-count");
search.addEventListener("input", () => {{
    const query = search.value.trim().toLocaleLowerCase();
    let visible = 0;
    for (const row of rows) {{
        const matches = row.cells[1].textContent.toLocaleLowerCase().includes(query);
        row.hidden = !matches;
        if (matches) visible++;
    }}
    rowCount.textContent = `${{visible.toLocaleString()}} of ${{rows.length.toLocaleString()}} players`;
}});
</script>
</body>
</html>
"""

    output_file = script_folder / "player_placings_report.html"
    output_file.write_text(report, encoding="utf-8")

    print(f"\nHTML report created: {output_file}")
    print(f"JSON folder: {data_folder}")
    print(f"JSON files processed: {len(json_files)}")
    print(f"Players found: {len(players)}")
    webbrowser.open(output_file.as_uri())


if __name__ == "__main__":
    main()