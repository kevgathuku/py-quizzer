from django.core.management.base import BaseCommand

from quizzer.snippetz.models import CodeSnippet, PythonVersion


VERSIONS = [
    (2, 7),
    (3, 0),
    (3, 1),
    (3, 2),
    (3, 3),
    (3, 5),
    (3, 6),
    (3, 7),
    (3, 8),
    (3, 10),
]

SNIPPETS = [
    {
        "title": "Dictionary Comprehension",
        "code": "result = {k: v for k, v in items.items()}",
        "version": (2, 7),
        "explanation": "Dictionary comprehensions were added in Python 2.7.",
    },
    {
        "title": "Set Literal",
        "code": "colors = {'red', 'green', 'blue'}",
        "version": (2, 7),
        "explanation": "Set literals using curly braces were introduced in Python 2.7.",
    },
    {
        "title": "Yield From",
        "code": "def chain(*iterables):\n    for it in iterables:\n        yield from it",
        "version": (3, 3),
        "explanation": "The 'yield from' expression was added in Python 3.3 (PEP 380).",
    },
    {
        "title": "Matrix Multiplication Operator",
        "code": "result = matrix_a @ matrix_b",
        "version": (3, 5),
        "explanation": "The @ operator for matrix multiplication was added in Python 3.5 (PEP 465).",
    },
    {
        "title": "F-String",
        "code": 'name = "world"\ngreeting = f"Hello, {name}!"',
        "version": (3, 6),
        "explanation": "F-strings (formatted string literals) were introduced in Python 3.6 (PEP 498).",
    },
    {
        "title": "Variable Annotations",
        "code": "count: int = 0\nnames: list[str] = []",
        "version": (3, 6),
        "explanation": "Variable annotations were introduced in Python 3.6 (PEP 526).",
    },
    {
        "title": "Walrus Operator",
        "code": "if (n := len(data)) > 10:\n    print(f'Too many: {n}')",
        "version": (3, 8),
        "explanation": "The walrus operator (:=) was added in Python 3.8 (PEP 572).",
    },
    {
        "title": "Positional-Only Parameters",
        "code": "def greet(name, /, greeting='Hello'):\n    return f'{greeting}, {name}'",
        "version": (3, 8),
        "explanation": "Positional-only parameters (/) were added in Python 3.8 (PEP 570).",
    },
    {
        "title": "Structural Pattern Matching",
        "code": "match command:\n    case 'quit':\n        quit_game()\n    case 'go' | 'move':\n        move_player()",
        "version": (3, 10),
        "explanation": "Structural pattern matching (match/case) was added in Python 3.10 (PEP 634).",
    },
    {
        "title": "Union Type with Pipe",
        "code": "def square(number: int | float) -> int | float:\n    return number ** 2",
        "version": (3, 10),
        "explanation": "The | operator for union types was added in Python 3.10 (PEP 604).",
    },
    {
        "title": "Print Function",
        "code": "print('Hello', 'World', sep=', ', end='!\\n')",
        "version": (3, 0),
        "explanation": "print became a function (instead of a statement) in Python 3.0 (PEP 3105).",
    },
    {
        "title": "Extended Iterable Unpacking",
        "code": "first, *middle, last = [1, 2, 3, 4, 5]",
        "version": (3, 0),
        "explanation": "Extended iterable unpacking with * was added in Python 3.0 (PEP 3132).",
    },
    {
        "title": "OrderedDict",
        "code": "from collections import OrderedDict\n\nod = OrderedDict()\nod['first'] = 1\nod['second'] = 2",
        "version": (3, 1),
        "explanation": "collections.OrderedDict was added in Python 3.1.",
    },
    {
        "title": "Argparse Module",
        "code": "import argparse\n\nparser = argparse.ArgumentParser()\nparser.add_argument('--verbose', action='store_true')\nargs = parser.parse_args()",
        "version": (3, 2),
        "explanation": "argparse replaced optparse as the recommended CLI parser in Python 3.2.",
    },
    {
        "title": "Concurrent Futures",
        "code": "from concurrent.futures import ThreadPoolExecutor\n\nwith ThreadPoolExecutor(max_workers=4) as pool:\n    results = pool.map(process, items)",
        "version": (3, 2),
        "explanation": "The concurrent.futures module was added in Python 3.2 (PEP 3148).",
    },
    {
        "title": "Async/Await",
        "code": "import asyncio\n\nasync def fetch_data(url):\n    await asyncio.sleep(1)\n    return 'data'",
        "version": (3, 5),
        "explanation": "async/await syntax was added in Python 3.5 (PEP 492).",
    },
    {
        "title": "Type Hints",
        "code": "def greeting(name: str) -> str:\n    return 'Hello ' + name",
        "version": (3, 5),
        "explanation": "Type hints were added in Python 3.5 (PEP 484).",
    },
    {
        "title": "Underscores in Numeric Literals",
        "code": "population = 7_900_000_000\nhex_addr = 0xFF_FF_FF_FF",
        "version": (3, 6),
        "explanation": "Underscores in numeric literals for readability were added in Python 3.6 (PEP 515).",
    },
    {
        "title": "Data Classes",
        "code": "from dataclasses import dataclass\n\n@dataclass\nclass Point:\n    x: float\n    y: float",
        "version": (3, 7),
        "explanation": "The dataclasses module was added in Python 3.7 (PEP 557).",
    },
    {
        "title": "Dictionary Ordering Guaranteed",
        "code": "d = {}\nd['first'] = 1\nd['second'] = 2\nassert list(d.keys()) == ['first', 'second']",
        "version": (3, 7),
        "explanation": "Dictionary insertion order was guaranteed by the language spec in Python 3.7.",
    },
]


class Command(BaseCommand):
    help = "Seed the database with Python versions and code snippets"

    def handle(self, *args, **options):
        version_objects = {}
        for major, minor in VERSIONS:
            obj, created = PythonVersion.objects.get_or_create(
                major=major, minor=minor
            )
            version_objects[(major, minor)] = obj
            if created:
                self.stdout.write(f"  Created Python {obj}")

        for snippet_data in SNIPPETS:
            version = version_objects[snippet_data["version"]]
            _, created = CodeSnippet.objects.get_or_create(
                title=snippet_data["title"],
                defaults={
                    "code": snippet_data["code"],
                    "first_appearance": version,
                    "explanation": snippet_data["explanation"],
                },
            )
            if created:
                self.stdout.write(f"  Created snippet: {snippet_data['title']}")

        self.stdout.write(self.style.SUCCESS("Seed complete."))
