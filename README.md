# MTG Commander Decks

My Commander/EDH deck collection with deck data and a price checker.

## Decks

| Commander | Colors | Bracket | Cards |
|-----------|--------|---------|-------|
| Gishath, Sun's Avatar | Naya | 3 | 100 |
| Kokusho, the Evening Star | Mono-Black | 3 | 100 |
| Kura, the Boundless Sky | Green | 3 | 100 |
| Magda, Brazen Outlaw | Red | 3 | 100 |
| Minn, Wily Illusionist | Blue | 3 | 100 |
| Omnath, Locus of Rage | Gruul | 3 | 107 |
| Sephiroth, Fabled SOLDIER | Black | 3 | 100 |
| Seshiro the Anointed | Green | 3 | 100 |
| Takeno, Samurai General | Mono-White | 3 | 100 |
| The First Sliver | Five-Color | 3 | 100 |

Each deck has a JSON file (full card list with categories) and a markdown readme in `decks/`.

## Price Checker

Fetches current USD prices from the [Scryfall API](https://scryfall.com/docs/api).

```
python3 prices.py                        # price all decks
python3 prices.py omnath-locus-of-rage   # price one deck
python3 prices.py --cheapest             # use cheapest printing per card
```

Shows per-card prices, top 10 most expensive, cost by category, and a grand total across all decks.
