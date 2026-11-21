#!/usr/bin/env python3
"""Validate first-party gettext usage and catalog completeness."""

from __future__ import annotations

import ast
import argparse
import re
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SOURCE_ROOTS = (ROOT / 'apps', ROOT / 'project')
SOURCE_SUFFIXES = {'.py', '.html', '.js'}
CYRILLIC_RE = re.compile(r'[А-Яа-яЁё]')
FIXED_RUSSIAN_LOCALE_RE = re.compile(r'ru[-_]RU', re.IGNORECASE)
GETTEXT_RE = re.compile(
    r'(?:\$root\.)?i18n\.(?:p?gettext)\(\s*(?:[\'\"][^\'\"]*[\'\"]\s*,\s*)?'
    r'(?P<quote>[\'\"])(?P<message>(?:\\.|(?!\1).)*)(?P=quote)',
    re.S,
)
NGETTEXT_RE = re.compile(
    r'(?:\$root\.)?i18n\.ngettext\(\s*'
    r'(?P<q1>[\'\"])(?P<singular>(?:\\.|(?!\1).)*)(?P=q1)\s*,\s*'
    r'(?P<q2>[\'\"])(?P<plural>(?:\\.|(?!\3).)*)(?P=q2)',
    re.S,
)
FORBIDDEN_WIDGET_LOCALES = (
    'static/libs/fullcalendar/lang/ru.js',
    'static/libs/moment/locale/ru.js',
    'static/patches/select2/i18n/ru.js',
    'static/libs/smalot-bootstrap-datetimepicker/js/locales',
)


def relative(path: Path) -> str:
    return path.relative_to(ROOT).as_posix()


def first_party_sources():
    for base in SOURCE_ROOTS:
        for path in sorted(base.rglob('*')):
            if not path.is_file() or path.suffix.lower() not in SOURCE_SUFFIXES:
                continue
            parts = set(path.relative_to(ROOT).parts)
            if (
                'migrations' in parts
                or 'tests' in parts
                or path.name == 'tests.py'
                or path.name.startswith('test_')
            ):
                continue
            yield path


def po_entries(path: Path):
    entries = []
    for block in path.read_text(encoding='utf-8').split('\n\n'):
        lines = block.splitlines()

        def field(name):
            values = []
            collecting = False
            for line in lines:
                if line.startswith(name + ' '):
                    values = [line[len(name) + 1:]]
                    collecting = True
                elif collecting and line.startswith('"'):
                    values.append(line)
                elif collecting:
                    break
            if not values:
                return None
            return ''.join(ast.literal_eval(value) for value in values)

        msgid = field('msgid')
        if msgid is None:
            continue
        entries.append({
            'msgid': msgid,
            'plural': field('msgid_plural'),
            'translated': any(
                (line.startswith('msgstr ') or line.startswith('msgstr['))
                and ast.literal_eval(line.split(' ', 1)[1])
                for line in lines
            ),
            'fuzzy': any(line.startswith('#,') and 'fuzzy' in line for line in lines),
        })
    return entries


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument('--update-catalog', action='store_true')
    args = parser.parse_args()
    errors = []
    js_messages = set()
    js_plurals = set()
    references = {}

    for path in first_party_sources():
        text = path.read_text(encoding='utf-8', errors='replace')
        for pattern, label in ((CYRILLIC_RE, 'Cyrillic literal'), (FIXED_RUSSIAN_LOCALE_RE, 'fixed ru-RU locale')):
            match = pattern.search(text)
            if match:
                line = text.count('\n', 0, match.start()) + 1
                errors.append(f'{relative(path)}:{line}: {label}')
        if path.suffix.lower() in {'.html', '.js'}:
            for match in GETTEXT_RE.finditer(text):
                message = ast.literal_eval(match.group('quote') + match.group('message') + match.group('quote'))
                js_messages.add(message)
                references.setdefault(message, set()).add(
                    f'{relative(path)}:{text.count(chr(10), 0, match.start()) + 1}'
                )
            for match in NGETTEXT_RE.finditer(text):
                singular = ast.literal_eval(match.group('q1') + match.group('singular') + match.group('q1'))
                plural = ast.literal_eval(match.group('q2') + match.group('plural') + match.group('q2'))
                js_messages.add(singular)
                js_plurals.add((singular, plural))
                references.setdefault(singular, set()).add(
                    f'{relative(path)}:{text.count(chr(10), 0, match.start()) + 1}'
                )

    for locale_path in FORBIDDEN_WIDGET_LOCALES:
        candidate = ROOT / locale_path
        if candidate.is_file() or (candidate.is_dir() and any(candidate.iterdir())):
            errors.append(f'widget locale must come from gettext, not {locale_path}')

    django_entries = po_entries(ROOT / 'locale/ru/LC_MESSAGES/django.po')
    djangojs_entries = po_entries(ROOT / 'locale/ru/LC_MESSAGES/djangojs.po')
    for catalog, entries in (('django.po', django_entries), ('djangojs.po', djangojs_entries)):
        for entry in entries:
            if not entry['msgid']:
                continue
            if entry['fuzzy']:
                errors.append(f'{catalog}: fuzzy translation for {entry["msgid"]!r}')
            if not entry['translated']:
                errors.append(f'{catalog}: untranslated message {entry["msgid"]!r}')

    catalog_messages = {entry['msgid'] for entry in djangojs_entries}
    catalog_plurals = {(entry['msgid'], entry['plural']) for entry in djangojs_entries if entry['plural']}
    if args.update_catalog:
        additions = []

        def po_quote(value):
            return '"' + value.replace('\\', '\\\\').replace('"', '\\"').replace('\n', '\\n') + '"'

        plural_by_singular = dict(js_plurals)
        for message in sorted(js_messages - catalog_messages):
            block = ['#: ' + ' '.join(sorted(references[message])), 'msgid ' + po_quote(message)]
            plural = plural_by_singular.get(message)
            if plural:
                block.extend(['msgid_plural ' + po_quote(plural)] + [f'msgstr[{index}] ""' for index in range(4)])
            else:
                block.append('msgstr ""')
            additions.append('\n'.join(block))
        for singular, plural in sorted(js_plurals - catalog_plurals):
            if singular in catalog_messages:
                errors.append(
                    f'djangojs.po cannot add plural {singular!r}: a singular entry already exists'
                )
        if additions and not errors:
            catalog_path = ROOT / 'locale/ru/LC_MESSAGES/djangojs.po'
            existing = catalog_path.read_text(encoding='utf-8').rstrip()
            catalog_path.write_text(existing + '\n\n' + '\n\n'.join(additions) + '\n', encoding='utf-8')
        if errors:
            for error in errors:
                print(f'ERROR: {error}', file=sys.stderr)
            return 1
        print(f'frontend catalog updated: {len(additions)} messages added')
        return 0

    for message in sorted(js_messages - catalog_messages):
        errors.append(f'djangojs.po: missing extracted frontend message {message!r}')
    for pair in sorted(js_plurals - catalog_plurals):
        errors.append(f'djangojs.po: missing plural entry {pair!r}')

    if errors:
        for error in errors:
            print(f'ERROR: {error}', file=sys.stderr)
        return 1
    print(
        f'frontend i18n passed: {len(js_messages)} messages, {len(js_plurals)} plurals, '
        'no first-party Russian literals or widget locale bundles'
    )
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
