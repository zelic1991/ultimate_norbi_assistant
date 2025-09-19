# Ultimate Norbi Assistant

Ein persönlicher VS Code & OpenAI gestützter Entwicklungs-Assistent.  
Enthält Skripte, Policies und Automatisierungen mit integrierten Quality Gates.

## Features

- **🤖 Intelligente Codegenerierung** mit Policy-gesteuerten Qualitätsregeln
- **🔍 Code-Critic-System** mit Syntax-, Lint- und Type-Checking
- **⚡ Performance-Profile** für verschiedene Anwendungsfälle
- **📁 Template-System** mit intelligenten Vorschlägen
- **👀 Preview-Modus** mit Warn-Only Quality Gates
- **🔧 Mehrsprachige Unterstützung** (Python, PowerShell, JavaScript)

## Quickstart

```bash
git clone https://github.com/zelic1991/ultimate_norbi_assistant.git
cd ultimate_norbi_assistant
python -m pip install PyYAML

# Demo der Features ausführen
python demo.py

# Verfügbare Profile anzeigen
python -m src.codegen --list-profiles

# Verfügbare Templates anzeigen  
python -m src.codegen --list-templates

# Code-Analyse im Preview-Modus
python -m src.codegen --preview your_file.py

# Template erstellen
python -m src.codegen --create-template fastapi ./my-api
```

## Kern-Komponenten

### Code Critic (`src/critic.py`)
- Multi-language Code-Qualitätsanalyse
- Syntax-, Lint- und Type-Checking
- Warn-Only-Modus für Preview-Flows
- Umfassende Fehlerberichterstattung

### Code Generation (`src/codegen.py`)
- Hauptorchestrator für Codegenerierung
- Integrierte Quality Gates
- Preview/Apply-Modi
- Policy-gesteuerte Konfiguration

### Performance Profile (`src/profiles.py`)
- `default` - Ausgewogene Performance und Qualität
- `fast` - Schnelle Analyse mit minimalen Checks
- `strict` - Umfassende Qualitätsprüfungen
- `development` - Entwicklerfreundlich mit Warnungen

### Template System (`src/templates.py`)
- FastAPI REST API Services
- Background Worker/CLI Applications
- React Frontend Components
- Python Library Packages
- Intelligente kontextbasierte Vorschläge

## CLI-Befehle

```bash
# Code analysieren
python -m src.codegen --preview files...

# Mit spezifischem Profil
python -m src.codegen --profile fast --preview files...

# Template-Vorschläge
python -m src.codegen --suggest-template "REST API service"

# Aus Template erstellen
python -m src.codegen --create-template fastapi ./my-api

# Alle verfügbaren Optionen
python -m src.codegen --help
```

## Konfiguration

### Policy-Datei (`POLICIES/codegen_policy.yaml`)
Definiert Regeln, Einschränkungen und Richtlinien für automatisierte Codegenerierung.

### System-Prompt (`prompts/system_codegen.md`)
KI-Prompt für intelligente, minimale Codeänderungen.

## Tests

```bash
python -m pytest tests/ -v
```

## Architektur

Das System folgt dem Prinzip minimaler, chirurgischer Änderungen:

1. **Analyse** - Verstehe den existierenden Codebase gründlich
2. **Planung** - Identifiziere die kleinste Änderung für das Ziel
3. **Qualitätsprüfung** - Führe Quality Gates aus (warn-only im Preview)
4. **Vorschau** - Zeige geplante Änderungen und Empfehlungen
5. **Anwendung** - Führe Änderungen mit Validierung durch

## Entwicklung

```bash
# Entwicklungsumgebung einrichten
python -m pip install -r requirements.txt

# Code-Qualität prüfen
python -m src.critic src/

# Demo ausführen
python demo.py
```
