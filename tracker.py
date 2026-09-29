import threading
import requests

from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button
from kivy.uix.scrollview import ScrollView
from kivy.core.window import Window
from kivy.clock import Clock

Window.clearcolor = (0.06, 0.06, 0.1, 1)

API_KEY = "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzUxMiIsImtpZCI6IjI4YTMxOGY3LTAwMDAtYTFlYi03ZmExLTJjNzQzM2M2Y2NhNSJ9.eyJpc3MiOiJzdXBlcmNlbGwiLCJhdWQiOiJzdXBlcmNlbGw6Z2FtZWFwaSIsImp0aSI6ImVhYmMzMWVhLWNlZjgtNDkxYi1iNTUzLTU5ODBkN2YxNzk1YSIsImlhdCI6MTc5MDY2NjI0OCwic3ViIjoiZGV2ZWxvcGVyLzdkODk2YzY5LTlmZjAtNGJhMy05MTJlLWYzOWY3ZDI2OGViZSIsInNjb3BlcyI6WyJicmF3bHN0YXJzIl0sImxpbWl0cyI6W3sidGllciI6ImRldmVsb3Blci9zaWx2ZXIiLCJ0eXBlIjoidGhyb3R0bGluZyJ9LHsiY2lkcnMiOlsiMTA5LjI1Mi44LjQ4Il0sInR5cGUiOiJjbGllbnQifV19.nYkVvh1ONUJrLLLl7tE6UGICGObzpt19CGPQ8YJ2WGpsjyy4Kq3G-eRLNszD05jHKyPbxAjPuW_2jwh9FUccZQ"
BASE = "https://api.brawlstars.com/v1"
HEADERS = {"Authorization": f"Bearer {API_KEY}"}


def api_get(endpoint):
    try:
        r = requests.get(BASE + endpoint, headers=HEADERS, timeout=15)
        if r.status_code != 200:
            return f"Ошибка {r.status_code}: {r.text[:100]}"
        return r.json()
    except Exception as e:
        return f"Ошибка сети: {e}"


def build_report(tag_input):
    tag = tag_input.replace("#", "%23").strip()

    data = api_get(f"/players/{tag}")
    if not isinstance(data, dict):
        return str(data)

    lines = []
    lines.append(f"=== {data.get('name', '?')} ===")
    lines.append(f"Тег: {data.get('tag', '?')}")
    lines.append("")
    lines.append(f"Кубки: {data.get('trophies', '?')}")
    lines.append(f"Максимум: {data.get('highestTrophies', '?')}")
    lines.append(f"Уровень: {data.get('expLevel', '?')}")
    lines.append(f"Победы 3v3: {data.get('3vs3Victories', '?')}")
    lines.append(f"Победы соло: {data.get('soloVictories', '?')}")
    lines.append(f"Победы дуо: {data.get('duoVictories', '?')}")

    club = data.get("club")
    if club:
        lines.append(f"Клуб: {club.get('name', '?')} ({club.get('tag', '?')})")

    brawlers = data.get("brawlers", [])
    if brawlers:
        top = sorted(brawlers, key=lambda x: x.get("trophies", 0), reverse=True)[:3]
        lines.append("")
        lines.append("--- Топ-3 бойца ---")
        for b in top:
            lines.append(f"{b.get('name', '?')}: {b.get('trophies', 0)} кубков, сила {b.get('power', '?')}")

    battles = api_get(f"/players/{tag}/battlelog")
    if isinstance(battles, dict):
        items = battles.get("items", [])
        if items:
            lines.append("")
            lines.append("--- Последние бои ---")
            for b in items[:5]:
                mode = b.get("event", {}).get("mode", "?")
                result = b.get("battle", {}).get("result", "?")
                lines.append(f"{mode} — {result}")

    return "\n".join(lines)


class TrackerApp(App):
    def build(self):
        root = BoxLayout(orientation="vertical", padding=20, spacing=10)

        title = Label(
            text="[b]Brawl Tracker[/b]",
            markup=True,
            size_hint=(1, 0.1),
            color=(0.4, 0.9, 1, 1)
        )
        root.add_widget(title)

        self.input = TextInput(
            hint_text="Введи тег, например #G0QRQYJVL",
            multiline=False,
            size_hint=(1, 0.1),
            background_color=(0.15, 0.15, 0.2, 1),
            foreground_color=(1, 1, 1, 1)
        )
        root.add_widget(self.input)

        btn = Button(
            text="Показать",
            size_hint=(1, 0.12),
            background_color=(0.2, 0.7, 0.4, 1)
        )
        btn.bind(on_press=self.on_click)
        root.add_widget(btn)

        scroll = ScrollView(size_hint=(1, 0.68))
        self.output = Label(
            text="",
            size_hint_y=None,
            halign="left",
            valign="top",
            color=(0.95, 0.95, 0.95, 1)
        )
        self.output.bind(width=lambda *x: setattr(self.output, "text_size", (self.output.width - 20, None)))
        self.output.bind(texture_size=lambda *x: setattr(self.output, "height", self.output.texture_size[1] + 20))
        scroll.add_widget(self.output)
        root.add_widget(scroll)

        return root

    def on_click(self, instance):
        tag = self.input.text.strip()
        if not tag:
            self.output.text = "Введи тег игрока"
            return
        if not tag.startswith("#"):
            tag = "#" + tag
        self.output.text = "Загрузка..."
        threading.Thread(target=self.fetch, args=(tag,), daemon=True).start()

    def fetch(self, tag):
        result = build_report(tag)
        Clock.schedule_once(lambda dt: setattr(self.output, "text", result))


if __name__ == "__main__":
    TrackerApp().run()
