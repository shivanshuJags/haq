"""Try vector search with a few realistic queries (incl. Hinglish).

Run from the project root (after db.load):
    python -m scripts.try_search
    python -m scripts.try_search "mujhe padhai ke liye paise chahiye" IN Bihar
"""
import sys

from core.search import search

EXAMPLES = [
    ("mujhe college ki padhai ke liye paise chahiye", "IN", "Bihar"),
    ("papa kisan hain, kheti ke liye madad chahiye", "IN", "Uttar Pradesh"),
    ("meri maa 72 saal ki hain, ilaaj ka kharcha nahi utha sakte", "IN", "Bihar"),
    ("I'm a single mum working part time and struggling with rent", "UK", None),
    ("I look after my disabled brother full time", "UK", None),
]


def show(query: str, country: str, region: str | None) -> None:
    print(f"\n> {query}  [{country}{', ' + region if region else ''}]")
    for row in search(query, country, region, limit=5):
        where = ", ".join(row["regions"]) if row["regions"] else "national"
        print(f"   {row['similarity']:.2f}  {row['name'][:70]}  ({where})")


if __name__ == "__main__":
    if len(sys.argv) > 1:
        show(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else "IN", sys.argv[3] if len(sys.argv) > 3 else None)
    else:
        for example in EXAMPLES:
            show(*example)
