#!/usr/bin/env python3
"""Fetch card prices from Scryfall for a deck or all decks.

Usage:
    python3 prices.py                          # price all decks
    python3 prices.py omnath-locus-of-rage     # price one deck (by filename stem)
    python3 prices.py --cheapest               # use cheapest printing per card
"""

import json
import os
import ssl
import sys
import time
import urllib.request
import urllib.parse
import urllib.error

DECKS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "decks")
SCRYFALL_API = "https://api.scryfall.com"

# Scryfall asks for 50-100ms between requests
REQUEST_DELAY = 0.1

# Fix SSL on macOS Python 3.8 — use system cert bundle
SSL_CONTEXT = ssl.create_default_context()
for cert_path in ["/etc/ssl/cert.pem", "/etc/ssl/certs/ca-certificates.crt"]:
    if os.path.exists(cert_path):
        SSL_CONTEXT.load_verify_locations(cert_path)
        break


def fetch_card(name, cheapest=False):
    """Fetch card data from Scryfall. Returns (price_usd, set_name) or (None, None)."""
    endpoint = "/cards/named"
    params = urllib.parse.urlencode({"fuzzy": name})
    url = f"{SCRYFALL_API}{endpoint}?{params}"

    try:
        req = urllib.request.Request(url, headers={"User-Agent": "MTGDeckTracker/1.0"})
        with urllib.request.urlopen(req, context=SSL_CONTEXT) as resp:
            data = json.loads(resp.read().decode())

        price = data.get("prices", {}).get("usd")
        set_name = data.get("set_name", "Unknown")

        if cheapest and price:
            # Check prints_search_uri for cheaper options
            prints_uri = data.get("prints_search_uri")
            if prints_uri:
                try:
                    req2 = urllib.request.Request(prints_uri, headers={"User-Agent": "MTGDeckTracker/1.0"})
                    with urllib.request.urlopen(req2, context=SSL_CONTEXT) as resp2:
                        prints_data = json.loads(resp2.read().decode())
                    best_price = float(price)
                    best_set = set_name
                    for printing in prints_data.get("data", []):
                        p = printing.get("prices", {}).get("usd")
                        if p and float(p) < best_price:
                            best_price = float(p)
                            best_set = printing.get("set_name", "Unknown")
                    price = str(best_price)
                    set_name = best_set
                    time.sleep(REQUEST_DELAY)
                except Exception:
                    pass

        return (float(price) if price else None, set_name)
    except urllib.error.HTTPError as e:
        if e.code == 404:
            return (None, f"NOT FOUND: {name}")
        raise
    except Exception as e:
        return (None, f"ERROR: {e}")


def price_deck(deck_path, cheapest=False):
    """Price all cards in a deck file. Returns (deck_data, priced_cards, total)."""
    with open(deck_path) as f:
        deck = json.load(f)

    priced = []
    total = 0.0
    not_found = []

    cards = deck["cards"]
    print(f"\n{'='*60}")
    print(f"  {deck['name']}")
    print(f"  Bracket {deck['bracket']} | {deck['color_identity']} | {deck['card_count']} cards")
    print(f"{'='*60}\n")

    # Skip basics for pricing
    basics = {"Forest", "Mountain", "Plains", "Island", "Swamp", "Wastes"}

    for card in cards:
        name = card["name"]
        qty = card["quantity"]

        if name in basics:
            priced.append({"name": name, "quantity": qty, "price": 0, "total": 0, "set": "Basic", "category": card["category"]})
            continue

        price, set_name = fetch_card(name, cheapest=cheapest)
        time.sleep(REQUEST_DELAY)

        if price is not None:
            card_total = price * qty
            total += card_total
            priced.append({"name": name, "quantity": qty, "price": price, "total": card_total, "set": set_name, "category": card["category"]})
            print(f"  ${price:>8.2f}  {name}")
        else:
            not_found.append(name)
            priced.append({"name": name, "quantity": qty, "price": None, "total": 0, "set": set_name, "category": card["category"]})
            print(f"  {'???':>9}  {name}  ({set_name})")

    # Sort by price descending for the summary
    priced_sorted = sorted(priced, key=lambda c: c.get("total") or 0, reverse=True)

    print(f"\n{'-'*60}")
    print(f"  TOTAL: ${total:.2f}")
    if not_found:
        print(f"  Could not price: {', '.join(not_found)}")
    print()

    # Top 10 most expensive
    print("  Top 10 most expensive:")
    for i, c in enumerate(priced_sorted[:10]):
        if c["price"]:
            print(f"    {i+1:>2}. ${c['price']:>7.2f}  {c['name']}")

    # Cost by category
    categories = {}
    for c in priced:
        cat = c["category"]
        if cat not in categories:
            categories[cat] = 0.0
        categories[cat] += c.get("total") or 0

    print(f"\n  Cost by category:")
    for cat, cost in sorted(categories.items(), key=lambda x: x[1], reverse=True):
        print(f"    {cat:<16} ${cost:>8.2f}")

    print()
    return deck, priced, total


def main():
    cheapest = "--cheapest" in sys.argv
    args = [a for a in sys.argv[1:] if not a.startswith("--")]

    if args:
        # Price specific deck(s)
        for slug in args:
            path = os.path.join(DECKS_DIR, f"{slug}.json")
            if not os.path.exists(path):
                print(f"Deck not found: {path}")
                continue
            price_deck(path, cheapest=cheapest)
    else:
        # Price all decks
        files = sorted(f for f in os.listdir(DECKS_DIR) if f.endswith(".json"))
        if not files:
            print("No decks found in", DECKS_DIR)
            return

        all_totals = []
        for fname in files:
            deck, priced, total = price_deck(os.path.join(DECKS_DIR, fname), cheapest=cheapest)
            all_totals.append((deck["name"], total, deck["bracket"]))

        if len(all_totals) > 1:
            print(f"\n{'='*60}")
            print("  ALL DECKS SUMMARY")
            print(f"{'='*60}")
            grand = 0
            for name, total, bracket in all_totals:
                print(f"  B{bracket}  ${total:>8.2f}  {name}")
                grand += total
            print(f"  {'':>3} ${grand:>8.2f}  GRAND TOTAL")
            print()


if __name__ == "__main__":
    main()
