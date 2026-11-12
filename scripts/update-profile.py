#!/usr/bin/env python3
"""Render a self-contained profile card from public GitHub data only."""
import json
import os
from datetime import datetime, timezone
from html import escape
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[1]
USERNAME = "kanuwrld"


def github(path):
    headers = {"Accept": "application/vnd.github+json", "User-Agent": "kanuwrld-profile", "X-GitHub-Api-Version": "2022-11-28"}
    token = os.environ.get("GH_TOKEN") or os.environ.get("GITHUB_TOKEN")
    if token:
        headers["Authorization"] = f"Bearer {token}"
    request = Request("https://api.github.com/" + path, headers=headers)
    with urlopen(request, timeout=25) as response:
        return json.load(response)


def collect():
    profile = github(f"users/{USERNAME}")
    repos = []
    for page in range(1, 101):
        batch = github(f"users/{USERNAME}/repos?type=owner&per_page=100&page={page}")
        repos.extend(repo for repo in batch if not repo["private"] and repo["owner"]["login"].lower() == USERNAME)
        if len(batch) < 100:
            break
    else:
        raise RuntimeError("Repository pagination limit reached")
    query = urlencode({"q": f"author:{USERNAME} is:pr is:merged is:public", "per_page": 1})
    pulls = github("search/issues?" + query)
    if pulls.get("incomplete_results"):
        raise RuntimeError("GitHub returned incomplete pull-request statistics")
    return {
        "username": USERNAME,
        "public_repositories": len(repos),
        "stars_on_original_repositories": sum(repo["stargazers_count"] for repo in repos if not repo["fork"]),
        "public_merged_pull_requests": pulls["total_count"],
        "followers": profile["followers"],
        "updated_at": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
        "scope": "Public repositories only; stars exclude forks. Merged PRs include public upstream contributions.",
    }


def render(data):
    values = [
        ("public repos", data["public_repositories"]),
        ("merged PRs", data["public_merged_pull_requests"]),
        ("stars", data["stars_on_original_repositories"]),
    ]
    rows = "\n".join(
        f'<text x="582" y="{155+i*110}" fill="#b9f36a" font-size="{min(66, 330 // max(1, len(format(value, ","))))}" font-weight="700" letter-spacing="-2">{value:,}</text>'
        f'<text x="584" y="{190+i*110}" fill="#9da7b3" font-size="28">{escape(label)}</text>'
        for i, (label, value) in enumerate(values)
    )
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="840" height="458" viewBox="0 0 840 458" role="img" aria-labelledby="title desc">
<title id="title">@kanuwrld</title>
<desc id="desc">A dancing pixel robot. {data['public_repositories']} public repositories, {data['public_merged_pull_requests']} merged public pull requests, and {data['stars_on_original_repositories']} stars on original repositories. Public GitHub data updated {escape(data['updated_at'])} UTC. Stars exclude forks.</desc>
<style>
 text {{ font-family: ui-monospace, SFMono-Regular, Consolas, 'Liberation Mono', monospace; }}
 .groove {{ animation: groove 1.4s steps(2,end) infinite; transform-origin: 628px 300px; }}
 .blink {{ animation: blink 3.2s steps(1,end) infinite; }}
 .spark {{ animation: spark 1.4s steps(2,end) infinite; }}
 @keyframes groove {{ 0%,100% {{ transform: rotate(-6deg) translateY(0); }} 50% {{ transform: rotate(6deg) translateY(-8px); }} }}
 @keyframes blink {{ 0%,92%,100% {{ opacity:1; }} 94%,98% {{ opacity:0; }} }}
 @keyframes spark {{ 0%,100% {{ opacity:.3; }} 50% {{ opacity:1; }} }}
 @media (prefers-reduced-motion: reduce) {{ .groove,.blink,.spark {{ animation:none; }} }}
</style>
<rect width="840" height="458" rx="12" fill="#0d1117"/>
<rect x=".5" y=".5" width="839" height="457" rx="12" fill="none" stroke="#30363d"/>
<path d="M0 50H840" stroke="#30363d"/>
<circle cx="28" cy="25" r="5" fill="#ff7b72"/><circle cx="46" cy="25" r="5" fill="#d29922"/><circle cx="64" cy="25" r="5" fill="#b9f36a"/>
<text x="805" y="32" text-anchor="end" fill="#c9d1d9" font-size="18">@kanuwrld</text>
{rows}
<g transform="translate(-777.4 -199) scale(1.7)">
<g class="spark" fill="#b9f36a"><path d="M500 179h6v6h-6zM494 185h6v6h-6zM506 185h6v6h-6zM500 191h6v6h-6z"/><path d="M750 249h6v6h-6zM744 255h6v6h-6zM756 255h6v6h-6zM750 261h6v6h-6z"/></g>
<g class="groove" shape-rendering="crispEdges">
<path d="M568 166h108v12h12v96H556v-96h12z" fill="#b9f36a"/>
<path d="M568 166h108v12H568zM556 178h12v24h-12zM676 178h12v24h-12z" fill="#e2ffb7"/>
<path d="M568 214h108v36H568z" fill="#151e17"/>
<g class="blink" fill="#e2ffb7"><path d="M580 222h24v8h-24zM640 222h24v8h-24z"/></g>
<path d="M604 252h36v8h-36z" fill="#151e17"/>
<path d="M580 274h84v48h-84zM568 282h12v24h-12zM664 282h12v24h-12z" fill="#a98bfa"/>
<path d="M556 282h12v12h-12zM544 270h12v24h-12zM532 258h12v24h-12zM520 246h12v24h-12zM676 282h12v12h-12zM688 270h12v24h-12zM700 258h12v24h-12zM712 246h12v24h-12z" fill="#b9f36a"/>
<path d="M520 234h12v12h-12zM712 234h12v12h-12z" fill="#e2ffb7"/>
</g>
<path d="M531 300h182l-14 52H545z" fill="#21262d" stroke="#484f58" stroke-width="2"/>
<path d="M519 352h206v8H519z" fill="#484f58"/>
<text x="622" y="333" text-anchor="middle" fill="#b9f36a" font-size="18" font-weight="bold">&gt;_</text>
</g>
</svg>'''


if __name__ == "__main__":
    stats = collect()
    svg = render(stats)
    (ROOT / "assets" / "profile.svg").write_text(svg, encoding="utf-8")
    (ROOT / "assets" / "stats.json").write_text(json.dumps(stats, indent=2) + "\n", encoding="utf-8")
    print(f"Updated public profile card for @{USERNAME}")
