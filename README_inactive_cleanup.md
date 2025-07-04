# Inactive Players Cleanup Script (mit Chunk-Überprüfung)

Dieses Python-Script findet alle Spieler in der Datenbank, die länger als eine bestimmte Anzahl von Tagen nicht angemeldet waren, **überprüft ob sie tatsächlich Chunks haben**, und generiert die entsprechenden `/admin unclaim_all` Kommandos nur für Spieler mit Claims.

## Features

- ✅ **Intelligente Chunk-Überprüfung**: Überprüft vor der Kommando-Generierung, ob Spieler tatsächlich Claims haben
- ✅ **RCON-Integration**: Kann Kommandos direkt über RCON ausführen
- ✅ **Batch-Verarbeitung**: Führt Kommandos in konfigurierbaren Batches aus, um Server-Überlastung zu vermeiden
- ✅ **Detaillierte Berichte**: Zeigt Anzahl der Claims pro Spieler
- ✅ **Sicherheitsmodus**: Dry-Run Modus zum Testen

## Verwendung

### Grundlegende Verwendung
```bash
# Aktiviere das virtuelle Environment
source venv/bin/activate

# Finde alle Spieler, die länger als 180 Tage (Standard) inaktiv sind und Chunks haben
python inactive_players_cleanup_with_chunks.py

# Finde Spieler, die länger als 300 Tage inaktiv sind
python inactive_players_cleanup_with_chunks.py --days 300
```

### RCON-Ausführung
```bash
# Führe Kommandos direkt über RCON aus (mit Bestätigung)
python inactive_players_cleanup_with_chunks.py --execute-rcon

# Mit kleineren Batches und längerer Wartezeit
python inactive_players_cleanup_with_chunks.py --execute-rcon --batch-size 3 --batch-delay 5
```

### Optionen

- `--days N`: Anzahl der Tage der Inaktivität (Standard: 180)
- `--output DATEI`: Speichere die Kommandos in eine Datei statt auf der Konsole auszugeben
- `--dry-run`: Zeige nur an, was gemacht werden würde, ohne tatsächlich Kommandos zu generieren
- `--show-details`: Zeige detaillierte Informationen über inaktive Spieler (Username, letzter Login, Tage inaktiv, Anzahl Claims)
- `--execute-rcon`: Führe Kommandos direkt über RCON aus
- `--batch-size N`: Anzahl der Kommandos pro RCON-Batch (Standard: 5)
- `--batch-delay N`: Wartezeit in Sekunden zwischen Batches (Standard: 2.0)
- `--skip-chunk-check`: Überspringe Chunk-Überprüfung (schneller aber weniger präzise)

### Beispiele

```bash
# Dry-Run mit Details für 180 Tage
python inactive_players_cleanup_with_chunks.py --dry-run --show-details

# Kommandos für 200 Tage Inaktivität in Datei speichern (nur Spieler mit Claims)
python inactive_players_cleanup_with_chunks.py --days 200 --output cleanup_commands.txt

# Direkte RCON-Ausführung für 300 Tage mit Bestätigung
python inactive_players_cleanup_with_chunks.py --days 300 --execute-rcon

# Ohne Chunk-Überprüfung (wie das ursprüngliche Script)
python inactive_players_cleanup_with_chunks.py --skip-chunk-check
```

## Ausgabe

Das Script zeigt an:
- Wie viele inaktive Spieler gefunden wurden
- Welche Spieler übersprungen werden (keine Claims)
- Detaillierte Claim-Informationen pro Spieler
- Generierte Kommandos im Format: `/admin unclaim_all <SpielerName>`

### Beispiel-Ausgabe:
```
Searching for players inactive for more than 300 days...

Found 3 inactive players:

Player RafDamian has 22 claimed chunks

Skipped 2 players with no claimed chunks:
  - <KingBBQ42>: No chunks claimed
  - RoseEnde705640: No chunks claimed

/admin unclaim_all RafDamian

Generated 1 commands (printed above)
```

## Chunk-Überprüfung

Das Script verwendet die gleiche NBT-Datei-Analyse wie das `main.py` Script:
- Liest `LMPlayers.dat` für Spieler-UUIDs
- Überprüft `ClaimedChunks.json` für tatsächliche Claims
- Zeigt Anzahl der Claims pro Spieler an
- Überspringt automatisch Spieler ohne Claims

## RCON-Ausführung

- Verbindet sich sicher zum Minecraft-Server
- Führt Kommandos in konfigurierbaren Batches aus
- Wartet zwischen Batches, um Server-Überlastung zu vermeiden
- Zeigt Serverantworten für jedes Kommando
- Fragt vor Ausführung nach Bestätigung

## Sicherheit

- Das Script führt nur Lesezugriffe auf die Datenbank durch
- Chunk-Überprüfung erfolgt read-only
- Die `--dry-run` Option ermöglicht sicheres Testen
- RCON-Ausführung erfordert explizite Bestätigung
- Batch-Verarbeitung verhindert Server-Überlastung
