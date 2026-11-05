#!/usr/bin/env python3
"""Build a public event feed from public event listings in Teplice and Usti nad Labem."""
from __future__ import annotations
import hashlib, json, re, sys
from datetime import datetime, timedelta
from pathlib import Path
from urllib.parse import urljoin
from zoneinfo import ZoneInfo
import requests
from bs4 import BeautifulSoup

ROOT = Path(__file__).resolve().parents[1]
FEED_PATH = ROOT / "events.json"
PRAGUE = ZoneInfo("Europe/Prague")
SOURCES = [
    ("Teplice", "https://visitteplice.com/aktuality/"),
    ("Ústí nad Labem", "https://kamvusti.cz/"),
    ("Ústí nad Labem", "https://www.usti.cz/cz/volny-cas/kalendar-akci.html"),
]
DATE_RE = re.compile(r"(?<!\d)(\d{1,2})\s*[./]\s*(\d{1,2})(?:\s*[./]\s*(20\d{2}))?")
TIME_RE = re.compile(r"(?<!\d)([01]?\d|2[0-3])[:.]([0-5]\d)(?!\d)")
SKIP_TITLES = {"více o akci", "přečíst článek", "načíst další události", "více"}
HEADERS = {"User-Agent": "CoBudemeDelatEventsBot/1.0 (public event feed)"}

def category_for(text: str) -> str:
    value = text.casefold()
    if any(w in value for w in ("koncert", "recitál", "recital", "hudeb", "kapela", "festival", "jazz", "live")): return "concert"
    if any(w in value for w in ("divadl", "představení", "predstaveni", "činoher", "muzikál", "opera", "balet")): return "theater"
    if any(w in value for w in ("party", "párty", "ples", "taneční", "tanc", "klub", "dj ", "diskot")): return "party"
    if any(w in value for w in ("zahrad", "jarmark", "trh", "venkovní", "venkovni", "orchidej")): return "garden"
    return "other"

def clean(value: str) -> str:
    return re.sub(r"\s+", " ", value).strip()

def parse_date(text: str, now: datetime):
    matches = list(DATE_RE.finditer(text))
    if not matches: return None, None
    result = []
    for match in matches[:2]:
        day, month, year = match.groups()
        try: date = datetime(int(year or now.year), int(month), int(day), tzinfo=PRAGUE)
        except ValueError: continue
        if not year and date.date() < (now - timedelta(days=30)).date(): date = date.replace(year=date.year + 1)
        result.append(date)
    if not result: return None, None
    times = list(TIME_RE.finditer(text))
    if times: result[0] = result[0].replace(hour=int(times[0].group(1)), minute=int(times[0].group(2)))
    return result[0], result[1] if len(result) > 1 and result[1] > result[0] else None

def make_event(title, city, start, end, venue, source_url, image_url="", description=""):
    key = f"{title.casefold()}|{city}|{start.isoformat()}|{venue.casefold()}"
    event = {"id": hashlib.sha1(key.encode()).hexdigest()[:16], "title": title, "category": category_for(title + " " + description),
             "venue": venue or city, "city": city, "dateStart": start.isoformat(), "sourceUrl": source_url, "ticketUrl": source_url}
    if end: event["dateEnd"] = end.isoformat()
    if image_url: event["imageUrl"] = image_url
    if description: event["description"] = description[:400]
    return event

def extract_jsonld(soup, city, page_url, now):
    found = []
    def walk(node):
        if isinstance(node, dict):
            types = node.get("@type", [])
            if isinstance(types, str): types = [types]
            if any(str(t).casefold().endswith("event") for t in types):
                try: start = datetime.fromisoformat(str(node["startDate"]).replace("Z", "+00:00")).astimezone(PRAGUE)
                except (ValueError, TypeError, KeyError): start = None
                if start and start >= now:
                    loc = node.get("location", {})
                    if isinstance(loc, list): loc = loc[0] if loc else {}
                    venue = loc.get("name", "") if isinstance(loc, dict) else ""
                    address = loc.get("address", {}) if isinstance(loc, dict) else {}
                    locality = address.get("addressLocality", "") if isinstance(address, dict) else ""
                    if locality and city.casefold() not in locality.casefold(): return
                    end = None
                    try: end = datetime.fromisoformat(str(node.get("endDate")).replace("Z", "+00:00")).astimezone(PRAGUE)
                    except (ValueError, TypeError): pass
                    title = clean(str(node.get("name", "")))
                    url = urljoin(page_url, str(node.get("url") or page_url))
                    image = node.get("image", "")
                    if isinstance(image, list): image = image[0] if image else ""
                    if title: found.append(make_event(title, city, start, end, venue, url, urljoin(page_url, str(image)) if image else "", str(node.get("description", ""))))
            for value in node.values(): walk(value)
        elif isinstance(node, list):
            for value in node: walk(value)
    for script in soup.select('script[type="application/ld+json"]'):
        try: walk(json.loads(script.string or script.get_text()))
        except (json.JSONDecodeError, TypeError): pass
    return found

def extract_visit_teplice(soup, page_url, now):
    found = []
    for link in soup.find_all("a", href=True):
        title = clean(link.get_text(" ", strip=True))
        if not title or title.casefold() in SKIP_TITLES or len(title) < 3 or len(title) > 180: continue
        parent, card = link, None
        for _ in range(6):
            parent = parent.parent
            if not getattr(parent, "get_text", None): break
            text = clean(parent.get_text(" ", strip=True))
            if DATE_RE.search(text) and title.casefold() in text.casefold() and len(text) < 900:
                card = parent
                break
        if card is None: continue
        text = clean(card.get_text(" ", strip=True))
        start, end = parse_date(text, now)
        if not start or start < now: continue
        after = text.split(title, 1)[-1]
        match = re.search(r"((?:Krušnohorské divadlo|Dům kultury|Zahradní dům|Kino Květen|Botanická zahrada|regionální knihovna|Místo konání DDM|sportovní hala|Kulturní centrum)[^|]{0,100})", after, re.I)
        venue = clean(match.group(1)).strip(" .,-") if match else ""
        image = card.find("img")
        image_url = urljoin(page_url, image.get("src") or image.get("data-src") or "") if image else ""
        found.append(make_event(title, "Teplice", start, end, venue, urljoin(page_url, link["href"]), image_url))
    return found

def fetch_source(city, url, now):
    response = requests.get(url, headers=HEADERS, timeout=25)
    response.raise_for_status()
    soup = BeautifulSoup(response.text, "html.parser")
    events = extract_jsonld(soup, city, url, now)
    if city == "Teplice": events.extend(extract_visit_teplice(soup, url, now))
    # Basic fallback for accessible event anchors that include a date in their own text.
    for link in soup.find_all("a", href=True):
        label = clean(link.get_text(" ", strip=True))
        start, end = parse_date(label, now)
        if start and start >= now and 4 <= len(label) <= 180:
            title = clean(DATE_RE.sub("", label)).strip(" -|:")
            if len(title) >= 4 and title.casefold() not in SKIP_TITLES:
                events.append(make_event(title, city, start, end, city, urljoin(url, link["href"])))
    return events

def main():
    now = datetime.now(PRAGUE)
    gathered, failures = {}, []
    for city, url in SOURCES:
        try:
            items = fetch_source(city, url, now)
            for event in items: gathered[event["id"]] = event
            print(f"{url}: {len(items)} kandidátů")
        except Exception as exc:
            failures.append(f"{url}: {exc}")
            print(f"Zdroj selhal {url}: {exc}", file=sys.stderr)
    events = sorted(gathered.values(), key=lambda item: item["dateStart"])
    if not events and FEED_PATH.exists():
        print("Bez nalezených akcí; ponechávám poslední feed.", file=sys.stderr)
        return 0
    payload = {"updatedAt": now.isoformat(), "events": events, "sources": [{"city": c, "url": u} for c, u in SOURCES]}
    FEED_PATH.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Zapsáno {len(events)} akcí.")
    if failures: print(f"Selhalo {len(failures)} zdrojů.", file=sys.stderr)
    return 0

if __name__ == "__main__": raise SystemExit(main())
