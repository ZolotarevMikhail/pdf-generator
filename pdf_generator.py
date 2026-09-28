#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Генератор PDF-документов по шаблону.

Как работает:
  1. Показывает список файлов данных (CSV/JSON) из папки data.
  2. Показывает список HTML-шаблонов из папки templates.
  3. Вы выбираете файл данных, шаблон и номер документа (invoice_id).
  4. Скрипт собирает документ и сохраняет PDF в папку output, затем открывает его.

Запуск: python3 pdf_generator.py
"""

import csv
import html
import json
import os
import re
import subprocess
import sys
from pathlib import Path

BASE = Path(__file__).resolve().parent
DATA_DIR = BASE / "data"
TPL_DIR = BASE / "templates"
OUT_DIR = BASE / "output"


def ensure_dirs():
    """Создать папки проекта, если их нет."""
    for d in (DATA_DIR, TPL_DIR, OUT_DIR):
        d.mkdir(exist_ok=True)


def list_files(folder: Path, exts: set) -> list:
    """Файлы нужного типа в папке, по алфавиту."""
    return sorted(p for p in folder.iterdir() if p.suffix.lower() in exts)


def choose(title: str, options, to_text=str):
    """Пронумерованное меню в консоли, возвращает выбранный вариант."""
    if not options:
        raise SystemExit(f"{title} — ничего не найдено. Положите файл в нужную папку и запустите снова.")
    print(f"\n{title}")
    for i, opt in enumerate(options, 1):
        print(f"  {i}. {to_text(opt)}")
    while True:
        n = input(f"Номер ({'1-' + str(len(options))}): ").strip()
        if n.isdigit() and 1 <= int(n) <= len(options):
            return options[int(n) - 1]
        print("  Нет такого номера, попробуйте ещё раз")


def load_rows(path: Path) -> list:
    """Прочитать файл данных в список записей {колонка: значение}."""
    text = path.read_text(encoding="utf-8-sig")  # utf-8-sig срезает BOM из Excel
    if path.suffix.lower() == ".json":
        data = json.loads(text)
        if isinstance(data, dict):  # допускаем {"items": [...]}
            data = data.get("items") or data.get("data")
        if not isinstance(data, list):
            raise ValueError("JSON должен быть списком записей вида [ {...}, {...} ]")
        return data
    return list(csv.DictReader(text.splitlines()))


def group_by_invoice(rows: list) -> dict:
    """Собрать позиции по счетам: {invoice_id: [строки]} в порядке появления."""
    invoices = {}
    for r in rows:
        invoices.setdefault(r["invoice_id"], []).append(r)
    return invoices


def money(v: float) -> str:
    """Сумма с пробелами между тысячами: 31000 -> 31 000"""
    return f"{v:,.2f}".rstrip("0").rstrip(".").replace(",", " ")


def number(v: float) -> str:
    """Количество без лишних нулей: 2.0 -> 2"""
    return f"{v:,.1f}".rstrip("0").rstrip(".").replace(",", " ")


def to_float(text: str) -> float:
    """Строка из CSV в число: понимает '2', '2,5', '2 500'"""
    return float((text or "0").replace(" ", "").replace(",", ".") or 0)


def make_items(rows: list):
    """Строки таблицы для подстановки вместо {{ items }} + общая сумма."""
    lines, total = [], 0.0
    for i, r in enumerate(rows, 1):
        qty = to_float(r.get("qty", "0"))
        price = to_float(r.get("price", "0"))
        amount = qty * price
        total += amount
        lines.append(
            f"<tr><td>{i}</td>"
            f'<td class="name">{html.escape(r.get("item", ""))}</td>'
            f"<td>{number(qty)}</td><td>{money(price)}</td><td>{money(amount)}</td></tr>"
        )
    return "\n".join(lines), total


def render(template_text: str, rows: list) -> str:
    """Подставить данные в шаблон и вернуть готовый HTML."""
    items_html, total = make_items(rows)
    fields = {k: html.escape(v) for k, v in rows[0].items() if k != "item"}
    fields["items"] = items_html
    fields["total"] = money(total)

    def substitute(m):
        key = m.group(1)
        if key not in fields:
            raise KeyError(f"в шаблоне есть метка {{{{ {key} }}}}, но такой колонки в данных нет")
        return fields[key]

    return re.sub(r"\{\{\s*(\w+)\s*\}\}", substitute, template_text)


def generate_pdf(page_html: str, invoice_id: str) -> Path:
    """Сделать PDF из HTML через WeasyPrint."""
    from weasyprint import HTML
    out = OUT_DIR / f"{invoice_id}.pdf"
    HTML(string=page_html, base_url=str(BASE)).write_pdf(str(out))
    return out


def open_pdf(path: Path):
    """Открыть PDF системной программой (macOS / Windows / Linux)."""
    if sys.platform == "darwin":
        subprocess.run(["open", str(path)])
    elif os.name == "nt":
        os.startfile(str(path))
    else:
        subprocess.run(["xdg-open", str(path)], check=False)


def run():
    ensure_dirs()
    data_files = list_files(DATA_DIR, {".csv", ".json"})
    templates = list_files(TPL_DIR, {".html"})

    data_file = choose("Файлы данных (data):", data_files)
    template = choose("Шаблоны (templates):", templates)

    rows = load_rows(data_file)
    if not rows:
        raise SystemExit(f"Файл {data_file.name} пустой")
    if "invoice_id" not in rows[0]:
        raise SystemExit("В данных нет колонки invoice_id — без неё нельзя собрать документ")

    invoice_id = choose("Документы:", list(group_by_invoice(rows)))

    page = render(template.read_text(encoding="utf-8"), group_by_invoice(rows)[invoice_id])

    try:
        pdf = generate_pdf(page, invoice_id)
    except ImportError:
        raise SystemExit("Библиотека WeasyPrint не установлена. В терминале: pip install weasyprint")
    except OSError as e:
        raise SystemExit("WeasyPrint не запустился — обычно не хватает системных библиотек "
                         "(на macOS помогает: brew install pango). Подробности: " + str(e))

    print(f"\nГотово: {pdf}")
    open_pdf(pdf)


if __name__ == "__main__":
    try:
        run()
    except KeyboardInterrupt:
        print("\nОтменено")
