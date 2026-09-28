# Генератор PDF-документов по шаблону

Программа для малого бизнеса и фрилансеров: есть таблица с данными (счета, заказы)
и HTML-шаблон документа — по каждому документу программа сама собирает готовый PDF
и открывает его.

Никаких ручных копирований из Excel в бланк. Подставили таблицу — получили PDF.

## Что умеет

- Читает файлы данных в папке `data` — CSV и JSON.
- Читает HTML-шаблоны в папке `templates` (метки вида `{{ customer_name }}`).
- Показывает меню: файл данных → шаблон → номер документа (invoice_id).
- Собирает документ, считает итог по позициям и сохраняет PDF в `output`.
- Сразу открывает готовый PDF системной программой.
- Работает на macOS и Windows.

## Как запустить

### 1. Установить Python

macOS — с сайта [python.org](https://www.python.org/downloads/), версия 3.9 или новее.
Windows — там же, при установке отметьте галочку **Add Python to PATH**.

### 2. Установить библиотеку печати

Откройте терминал (в VS Code: Терминал → Создать терминал) и в папке проекта:

```
python3 -m venv venv
source venv/bin/activate        # macOS
pip install weasyprint
```

Windows (в PowerShell):

```
python -m venv venv
.\venv\Scripts\activate.ps1
pip install weasyprint
```

### 3. Системные библиотеки

**macOS:** нужен [Homebrew](https://brew.sh) и одна библиотека:

```
brew install pango
```

и запуск с указанием, где библиотека лежит:

```
DYLD_FALLBACK_LIBRARY_PATH=/opt/homebrew/lib python3 pdf_generator.py
```

**Windows:** понадобится GTK3 — установите по инструкции
[отсюда](https://github.com/tschoonj/GTK-for-Windows-Runtime-Environment-Installer/releases)
(скачать последний .exe, установить, везде Next).

### 4. Запуск

```
python3 pdf_generator.py        # macOS
python pdf_generator.py         # Windows
```

Дальше программа сама покажет меню: выберите файл данных, шаблон и номер документа.
Готовый PDF появится в папке `output` и откроется сам.

## Как добавить свой бланк

Скопируйте любой HTML-шаблон, положите его в `templates` и поставьте в текст метки:
`{{ invoice_id }}`, `{{ customer_name }}`, `{{ date }}` — поля из таблицы,
`{{ items }}` — место, где строится таблица позиций, `{{ total }}` — итог.
Названия полей должны совпадать с заголовками колонок вашего CSV.

## Структура проекта

```
pdf-generator
├── data/         файлы с данными (CSV, JSON)
├── templates/    HTML-шаблоны документов
├── output/       готовые PDF (появляются после запуска)
└── pdf_generator.py
```

## Тестовые данные

В `data/invoices.csv` лежат три демо-счёта (INV-001…INV-003) — на них можно
проверить работу до того, как подставите свои.