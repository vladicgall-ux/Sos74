from datetime import datetime, timedelta


def period_range(period: str):
    now = datetime.now()
    date_to_dt = now

    if period == "today":
        date_from_dt = now.replace(hour=0, minute=0, second=0, microsecond=0)
        title = "за сегодня"
    elif period == "yesterday":
        yesterday = now - timedelta(days=1)
        date_from_dt = yesterday.replace(hour=0, minute=0, second=0, microsecond=0)
        date_to_dt = yesterday.replace(hour=23, minute=59, second=59, microsecond=999999)
        title = "за вчера"
    elif period == "week":
        date_from_dt = (now - timedelta(days=now.weekday())).replace(
            hour=0, minute=0, second=0, microsecond=0
        )
        title = "за эту неделю"
    elif period == "last_week":
        this_monday = (now - timedelta(days=now.weekday())).replace(
            hour=0, minute=0, second=0, microsecond=0
        )
        date_from_dt = this_monday - timedelta(days=7)
        date_to_dt = this_monday - timedelta(microseconds=1)
        title = "за прошлую неделю"
    elif period == "month":
        date_from_dt = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        title = "за этот месяц"
    elif period == "last_month":
        first_this_month = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        date_to_dt = first_this_month - timedelta(microseconds=1)
        date_from_dt = date_to_dt.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        title = "за прошлый месяц"
    else:  # "all"
        date_from_dt = datetime(2000, 1, 1)
        title = "за всё время"

    return date_from_dt.isoformat(), date_to_dt.isoformat(), title


def format_order_date(iso_str: str) -> str:
    return datetime.fromisoformat(iso_str).strftime("%d.%m %H:%M")


REPORT_SEPARATOR = "➖➖➖➖➖➖➖➖➖"


def render_report(header: str, blocks: list, footer: str) -> str:
    def build(items):
        parts = [header]
        for block in items:
            parts.append(REPORT_SEPARATOR + "\n" + block)
        parts.append(REPORT_SEPARATOR)
        parts.append("\n" + footer)
        return "\n".join(parts)

    text = build(blocks)
    if len(text) <= 4000:
        return text

    # Trim whole order blocks (never mid-tag) so the HTML stays valid.
    remaining = list(blocks)
    note = "\n⚠️ Показаны не все заявки — список слишком длинный"
    while remaining and len(build(remaining)) + len(note) > 4000:
        remaining.pop()
    return build(remaining) + note
