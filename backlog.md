## Verbesserungs-Backlog

Dieser Verbesserungs-Backlog listet priorisierte Aufgaben für den Pilot-Agenten auf, inklusive klarer Meinungen, Impact und KPIs:

### A) Sofort (hoher Impact, geringe Komplexität)

1. **JSON-Logging + Request-IDs**
   - Wert: Nachvollziehbarkeit, schnellere Fehleranalyse.
   - KPI-Hebel: Mean Time to Recovery (MTTR) um 30–50 % senken, Incident-Klarheit erhöhen.

2. **Inline-Approvals in Telegram (Buttons)**
   - Wert: Freigaben in einem Klick, weniger Reibung.
   - KPI-Hebel: Decision→Action-Zeit um 40–60 % reduzieren.

3. **Projekt-Scoring "Aufräum-Kandidaten" (Inaktivität, Größe, Redundanz, Artefakte)**
   - Wert: Zielsicheres Entrümpeln statt Bauchgefühl.
   - KPI-Hebel: Speicherersparnis um 20–35 % erhöhen.

### B) Nächste Iteration (mittlerer Aufwand, großer Hebel)

4. **Glossar/Terminologie-Profil für dich** (z. B. Kelly-Light, CLV, „30-Punkte-Check“)
   - Wert: Weniger Rückfragen, bessere Intent-Erkennung.
   - KPI-Hebel: Intent-Accuracy von 95 % auf 98 % steigern.

5. **What-If-Simulator vor Mass-Edits**
   - Wert: Keine Überraschungen, klare Wirkung vorab.
   - KPI-Hebel: Rollbacks vermeiden, Vertrauen erhöhen.

6. **Täglicher KPI-Digest (kompakt)**
   - Wert: Führung auf einen Blick, kein Blackhole-Gefühl.
   - KPI-Hebel: Steuerungsqualität erhöhen, Blindzeiten reduzieren.

### C) Danach (strategisch, nachhaltiger Effekt)

7. **Adaptive Retention** (nutzungsbasiert: „heiß/warm/kalt“)
   - Wert: Platz sparen ohne Wertverlust.
   - KPI-Hebel: Netto-Speicherverbrauch um 25–40 % senken.

8. **Self-Learning Feedback-Loop** (Fehler → Regel)
   - Wert: Wiederholungsfehler vermeiden, Stil anpassen.
   - KPI-Hebel: Rückfragenquote senken, Ersttrefferquote erhöhen.

9. **Semantic Dedupe** (Inhalt statt Name)
   - Wert: Echte Doppelgänger finden, nicht nur identische Bytes.
   - KPI-Hebel: Dedupe-Quote von 95 % auf 98 % steigern.

10. **Playbooks** (Standardvorgänge in 3–5 Schritten)
   - Wert: „Einmal denken, immer anwenden“ – reproduzierbare Qualität.
   - KPI-Hebel: Durchlaufzeit je Routinejob um 30 % senken.

### D) Nice-to-have (wenn Kapazität da ist)

11. **SLOs/Fehlerbudgets** (z. B. ≤ 1 % Fehlversuche/Woche)

12. **Secrets-Scan & Policy-Gate** (Bevor etwas ins Repo fließt)

13. **Speech-Profil-Feinschliff** (dein Akzent, dein Tempo)

14. **Repo-Weit RAG-Suche** (Antworten mit Verweis auf Fundstellen)

15. **Release-Notes Auto-Writer** (Digest → Changelog)


### Klare Meinung – Was „am meisten knallt“

- Inline-Approvals + What-If bringen sofort Sicherheit und Speed.
- Glossar + Self-Learning sorgen dafür, dass der Agent „wie du denkt“.
- Adaptive Retention + Semantic Dedupe sparen Platz ohne Qualitätseinbußen.
- JSON-Logging + KPI-Digest beenden jede Intransparenz – du führst nach Zahlen.
