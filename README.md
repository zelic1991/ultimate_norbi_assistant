# Pilot Agent Repository

Dieses Repository enthält die Grundlage für deinen personalisierten Pilot‑Agenten. Es ist so aufgebaut, dass es in einer lokalen Entwicklungsumgebung (z. B. Visual Studio Code) sofort genutzt werden kann. Die Struktur folgt den Prinzipien aus deiner Vision: minimale Ordner‑Hierarchie, klare Verantwortungen und ein sauberer Daten‑Lifecycle.

## Struktur

```
pilot_agent_repo/
├── RAW/        # Eingangsdaten (temporär, nach kurzer Zeit komprimieren)
├── CURRENT/    # Eine Datei pro Thema; normalisierte Arbeitsstände
├── ARCHIVE/    # Sparsame Snapshots (z. B. monatlich)
├── POLICIES/   # Richtlinien und Konfigurationen im YAML‑Format
├── tasks/      # Python‑Module für Datenhygiene, Intent‑Engine und Orchestrierung
├── config.py   # Laden und Interpretieren der Richtlinien
├── main.py     # Einstiegspunkt zur Ausführung von Tasks
├── system_prompt.md   # Dienstanweisung für den Pilot‑Agenten
└── README.md   # Diese Datei
```

### Ordner
- **RAW/**: Hier landen neue Daten. Der Agent komprimiert diese Dateien automatisch, wenn sie älter als eine definierte Schwelle sind. Das spart Speicher ohne Informationsverlust.
- **CURRENT/**: Enthält den aktuellen Arbeitsstand pro Thema. Es gibt nur eine Datei pro Datensatz, damit kein „Datei‑Chaos” entsteht. Neue Daten werden hier hinein normalisiert.
- **ARCHIVE/**: Archiviert stabile Stände. Snapshots werden sparsam abgelegt (z. B. einmal pro Monat) und stehen für historische Analysen bereit.
- **POLICIES/**: Enthält YAML‑Dateien, die Regeln für die Arbeitsweise des Agenten definieren (z. B. Tonalität, Freigabe‑Schwellen oder Speicher‑Limits).
- **tasks/**: Python‑Module, die konkrete Aufgaben abbilden – etwa Daten komprimieren, Duplikate entfernen oder die Intent‑Engine bedienen.

## Wie du den Pilot‑Agenten nutzt

1. **Richtlinien definieren**: Passe die Dateien in `POLICIES/` an deine Bedürfnisse an. Beispielsweise kannst du in `policy.yaml` die Freigabe‑Stufen für riskante Aktionen festlegen oder definieren, welche Ordner erlaubt sind.
2. **System-Prompt konfigurieren**: Die Datei `system_prompt.md` enthält die Dienstanweisung für den Agenten. Diese wird als System‑Prompt geladen, um das Verhalten zu steuern. Bearbeite sie nur, wenn du den Stil oder die Kernaufgaben ändern möchtest.
3. **Konfiguration laden**: Das Modul `config.py` lädt YAML‑Richtlinien und macht sie den Tasks zugänglich. So kann z. B. der Datenbereiniger prüfen, ob eine Datei komprimiert werden soll.
4. **Tasks ausführen**: Mit `main.py` kannst du einzelne Tasks anstoßen. Beispiele:
   - `python main.py compress` – Komprimiert alle Daten in `RAW/`, die älter als die definierte Schwelle sind.
   - `python main.py dedupe` – Entfernt Duplikate in `CURRENT/`.
   - `python main.py validate` – Prüft die Struktur der CSV/Parquet‑Dateien, bevor sie weiterverarbeitet werden.
5. **Intent‑Engine erweitern**: Im Modul `intent_engine.py` findest du eine rudimentäre Umsetzung für die Erkennung von Absichten. Erweitere diese Logik, um natürliche Sprachbefehle in konkrete Aktionen zu übersetzen.

## Hinweise zur Weiterentwicklung

- **Autonomer Betrieb**: Nutze einen Scheduler (z. B. `cron` oder das Automations‑Tool), um Tasks regelmäßig auszuführen. Beim Löschen oder Massenänderungen solltest du immer eine Dry‑Run‑Simulation einbauen und Freigaben einholen.
- **Lernen und Feedback**: Baue eine einfache Feedback‑Schleife ein, die Korrekturen von dir als Regeln speichert. Dadurch wird der Agent mit der Zeit besser auf deine Sprachgewohnheiten abgestimmt.
- **Monitoring**: Füge Metriken hinzu (z. B. Anzahl bearbeiteter Dateien, Speicherersparnis, Fehlerraten), um die Leistung zu messen. Diese Metriken können in den täglichen/wöchentlichen Berichten verwendet werden.

<!--- Hinweis: Zusätzliches PowerShell-Skript-Snippet zum Update von .env könnten hier dokumentiert werden. -->

## Lizenz

Dieses Beispiel ist als Ausgangspunkt gedacht und steht unter keiner spezifischen Lizenz. Passe die Inhalte frei an deine Anforderungen an.