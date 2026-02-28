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
