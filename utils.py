from datetime import datetime, timedelta


def period_range(period: str):
    now = datetime.now()
    if period == "today":
        date_from = now.replace(hour=0, minute=0, second=0, microsecond=0).isoformat()
        title = "за сегодня"
    elif period == "week":
        date_from = (now - timedelta(days=now.weekday())).replace(
            hour=0, minute=0, second=0, microsecond=0
        ).isoformat()
        title = "за эту неделю"
    else:
        date_from = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0).isoformat()
        title = "за этот месяц"
    date_to = now.isoformat()
    return date_from, date_to, title


def format_order_date(iso_str: str) -> str:
    return datetime.fromisoformat(iso_str).strftime("%d.%m %H:%M")
