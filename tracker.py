import requests
import json
import os
from datetime import datetime
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.prompt import Prompt

console = Console()

API_KEY = "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzUxMiIsImtpZCI6IjI4YTMxOGY3LTAwMDAtYTFlYi03ZmExLTJjNzQzM2M2Y2NhNSJ9.eyJpc3MiOiJzdXBlcmNlbGwiLCJhdWQiOiJzdXBlcmNlbGw6Z2FtZWFwaSIsImp0aSI6ImVhYmMzMWVhLWNlZjgtNDkxYi1iNTUzLTU5ODBkN2YxNzk1YSIsImlhdCI6MTc5MDY2NjI0OCwic3ViIjoiZGV2ZWxvcGVyLzdkODk2YzY5LTlmZjAtNGJhMy05MTJlLWYzOWY3ZDI2OGViZSIsInNjb3BlcyI6WyJicmF3bHN0YXJzIl0sImxpbWl0cyI6W3sidGllciI6ImRldmVsb3Blci9zaWx2ZXIiLCJ0eXBlIjoidGhyb3R0bGluZyJ9LHsiY2lkcnMiOlsiMTA5LjI1Mi44LjQ4Il0sInR5cGUiOiJjbGllbnQifV19.nYkVvh1ONUJrLLLl7tE6UGICGObzpt19CGPQ8YJ2WGpsjyy4Kq3G-eRLNszD05jHKyPbxAjPuW_2jwh9FUccZQ"
BASE = "https://api.brawlstars.com/v1"
HEADERS = {"Authorization": f"Bearer {API_KEY}"}
HISTORY_FILE = "history.json"
REPORT_DIR = "reports"

# кэш ролей бойцов, чтобы не дёргать API каждый раз
_brawler_roles = None


def get(endpoint):
    r = requests.get(BASE + endpoint, headers=HEADERS, timeout=15)
    if r.status_code != 200:
        console.print(f"[bold red]Ошибка {r.status_code}:[/bold red] {r.text}")
        return None
    return r.json()


def load_brawler_roles():
    """Загружает роли всех бойцов один раз и кэширует"""
    global _brawler_roles
    if _brawler_roles is not None:
        return _brawler_roles

    data = get("/brawlers")
    if not data:
        _brawler_roles = {}
        return _brawler_roles

    roles = {}
    for item in data.get("items", []):
        name = item.get("name", "").upper()
        role = item.get("role", "Unknown")
        roles[name] = role

    _brawler_roles = roles
    return roles


def show_player(tag_input, report_lines=None):
    tag = tag_input.replace("#", "%23")
    data = get(f"/players/{tag}")
    if not data:
        return None

    panel = Panel.fit(
        f"[bold cyan]{data.get('name', '?')}[/bold cyan]\n"
        f"[yellow]Тег:[/yellow] {data.get('tag', '?')}",
        title="Профиль игрока",
        border_style="green"
    )
    console.print(panel)

    if report_lines is not None:
        report_lines.append(f"=== {data.get('name', '?')} ({data.get('tag', '?')}) ===")

    table = Table(title="Статистика", header_style="bold magenta")
    table.add_column("Параметр", style="cyan")
    table.add_column("Значение")
    rows = [
        ("Кубки", data.get("trophies", "?")),
        ("Максимум кубков", data.get("highestTrophies", "?")),
        ("Уровень опыта", data.get("expLevel", "?")),
        ("Победы 3v3", data.get("3vs3Victories", "?")),
        ("Победы соло", data.get("soloVictories", "?")),
        ("Победы дуо", data.get("duoVictories", "?")),
    ]
    for k, v in rows:
        table.add_row(k, str(v))
        if report_lines is not None:
            report_lines.append(f"{k}: {v}")
    console.print(table)

    club = data.get("club")
    if club:
        line = f"Клуб: {club.get('name', '?')} ({club.get('tag', '?')})"
        console.print(f"\n[bold green]Клуб:[/bold green] {club.get('name', '?')} ({club.get('tag', '?')})")
        if report_lines is not None:
            report_lines.append(line)
    else:
        console.print("\n[dim]Без клуба[/dim]")

    return data


def show_top_brawlers(tag_input, limit=10, role_filter=None, report_lines=None):
    tag = tag_input.replace("#", "%23")
    data = get(f"/players/{tag}")
    if not data:
        return

    brawlers = data.get("brawlers", [])
    if not brawlers:
        console.print("\n[dim]Бойцы не найдены[/dim]")
        return

    roles = load_brawler_roles()

    if role_filter:
        filtered = [b for b in brawlers if roles.get(b.get("name", "").upper()) == role_filter]
    else:
        filtered = brawlers

    if not filtered:
        console.print(f"\n[dim]Нет бойцов с ролью '{role_filter}'[/dim]")
        return

    brawlers_sorted = sorted(filtered, key=lambda x: x.get("trophies", 0), reverse=True)

    title = f"Топ-{limit} бойцов"
    if role_filter:
        title += f" ({role_filter})"

    table = Table(title=title, header_style="bold magenta")
    table.add_column("#", style="dim")
    table.add_column("Боец", style="cyan")
    table.add_column("Кубки", style="yellow")
    table.add_column("Сила", style="green")
    table.add_column("Роль", style="blue")

    top_slice = brawlers_sorted[:limit]
    trophies_sum = 0

    for i, b in enumerate(top_slice, 1):
        name = b.get("name", "?")
        trophies = b.get("trophies", 0)
        power = b.get("power", "?")
        role = roles.get(name.upper(), "?")
        trophies_sum += trophies

        table.add_row(str(i), name, str(trophies), str(power), role)

    console.print("\n")
    console.print(table)

    # среднее
    avg = trophies_sum // len(top_slice) if top_slice else 0
    console.print(f"[bold yellow]Среднее по топ-{len(top_slice)}: {avg} кубков[/bold yellow]")

    if report_lines is not None:
        report_lines.append(f"\n--- Топ-{limit} бойцов ---")
        for i, b in enumerate(top_slice, 1):
            report_lines.append(f"{i}. {b.get('name', '?')} — {b.get('trophies', 0)} кубков, сила {b.get('power', '?')}, роль {roles.get(b.get('name', '').upper(), '?')}")
        report_lines.append(f"Среднее: {avg}")


def show_battles(tag_input, report_lines=None):
    tag = tag_input.replace("#", "%23")
    data = get(f"/players/{tag}/battlelog")
    if not data:
        return
    items = data.get("items", [])
    if not items:
        console.print("\n[dim]Боёв не найдено[/dim]")
        return
    console.print("\n[bold yellow]Последние бои:[/bold yellow]")
    if report_lines is not None:
        report_lines.append("\n--- Последние бои ---")
    for b in items[:5]:
        mode = b.get("event", {}).get("mode", "?")
        result = b.get("battle", {}).get("result", "?")
        color = "green" if result == "victory" else "red" if result == "defeat" else "yellow"
        console.print(f"  [{color}]{mode}[/{color}] — {result}")
        if report_lines is not None:
            report_lines.append(f"{mode} — {result}")


def show_world_top(report_lines=None):
    """Показывает топ-1 игрока мира"""
    data = get("/rankings/global/players?limit=1")
    if not data:
        return

    items = data.get("items", [])
    if not items:
        console.print("\n[dim]Глобальный рейтинг недоступен[/dim]")
        return

    top1 = items[0]
    name = top1.get("name", "?")
    tag = top1.get("tag", "?")
    trophies = top1.get("trophies", "?")

    console.print(Panel.fit(
        f"[bold yellow]Топ-1 мира[/bold yellow]\n"
        f"[cyan]{name}[/cyan] ({tag})\n"
        f"[yellow]Кубки:[/yellow] {trophies}",
        border_style="yellow"
    ))

    if report_lines is not None:
        report_lines.append(f"\n--- Топ-1 мира ---")
        report_lines.append(f"{name} ({tag}) — {trophies} кубков")


def save_history(tag_input, trophies):
    entry = {
        "date": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "tag": tag_input,
        "trophies": trophies
    }
    history = []
    if os.path.exists(HISTORY_FILE):
        try:
            with open(HISTORY_FILE, "r") as f:
                history = json.load(f)
        except Exception:
            history = []
    history.append(entry)
    with open(HISTORY_FILE, "w") as f:
        json.dump(history, f, indent=2, ensure_ascii=False)
    console.print(f"\n[dim]✓ Запись в {HISTORY_FILE}[/dim]")


def show_history(tag_input):
    if not os.path.exists(HISTORY_FILE):
        return
    try:
        with open(HISTORY_FILE, "r") as f:
            history = json.load(f)
    except Exception:
        return
    entries = [e for e in history if e.get("tag") == tag_input]
    if len(entries) < 2:
        return
    first = entries[0]
    last = entries[-1]
    diff = last["trophies"] - first["trophies"]
    console.print(f"\n[bold yellow]Динамика:[/bold yellow]")
    console.print(f"  [dim]{first['date']}[/dim] — {first['trophies']}")
    console.print(f"  [dim]{last['date']}[/dim] — {last['trophies']}")
    if diff > 0:
        console.print(f"  [bold green]↑ +{diff}[/bold green]")
    elif diff < 0:
        console.print(f"  [bold red]↓ {diff}[/bold red]")
    else:
        console.print(f"  [yellow]= 0[/yellow]")


def save_report(tag_input, report_lines):
    """Сохраняет отчёт в файл"""
    if not os.path.exists(REPORT_DIR):
        os.makedirs(REPORT_DIR)

    safe_tag = tag_input.replace("#", "")
    filename = f"{REPORT_DIR}/report_{safe_tag}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"

    with open(filename, "w", encoding="utf-8") as f:
        f.write("\n".join(report_lines))

    console.print(f"\n[bold green]✓ Отчёт сохранён:[/bold green] {filename}")


def ask_role_filter():
    """Спрашивает, фильтровать ли по роли"""
    choice = Prompt.ask(
        "[bold cyan]Фильтр по роли?[/bold cyan] (Tank/Marksman/Assassin/Support/Damage Dealer/Artillery/Controller или Enter — без фильтра)",
        default=""
    )
    return choice.strip() if choice.strip() else None


if __name__ == "__main__":
    tag = Prompt.ask("[bold cyan]Тег игрока[/bold cyan]")

    role = ask_role_filter()

    report_lines = [f"Отчёт от {datetime.now().strftime('%Y-%m-%d %H:%M')}"]

    data = show_player(tag, report_lines)
    if data:
        show_top_brawlers(tag, limit=10, role_filter=role, report_lines=report_lines)
        show_battles(tag, report_lines=report_lines)
        show_world_top(report_lines=report_lines)
        save_history(tag, data.get("trophies", 0))
        show_history(tag)
        save_report(tag, report_lines)
