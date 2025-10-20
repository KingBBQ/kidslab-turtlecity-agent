# Datenbank-Verwaltung für TurtleCity Agent

## 📍 Wo ist die Datenbank?

Die Datenbank ist **lokal** gespeichert in:
```
/Users/kingbbq/src/kidslab-turtlecity-agent/db/players.db
```

## 🔄 Wie wird die Datenbank erstellt?

Die Datenbank wird **automatisch** von `main.py` erstellt, wenn der Agent startet:

1. **Automatische Erstellung**: Beim Start von `main.py` wird `database.initialize_database()` aufgerufen
2. **Automatische Updates**: Der Agent überwacht die Minecraft-Logs und aktualisiert die Datenbank bei:
   - Spieler-Login → `last_login` wird aktualisiert, `login_count` wird erhöht
   - Spieler-Logout → `last_logout` wird aktualisiert, `total_time` wird berechnet

## 📊 Datenbank-Struktur

```sql
CREATE TABLE players (
    username TEXT PRIMARY KEY,      -- Spielername
    last_login TEXT,                -- Letzter Login (YYYY-MM-DD HH:MM:SS)
    last_logout TEXT,               -- Letzter Logout (YYYY-MM-DD HH:MM:SS)
    total_time INTEGER DEFAULT 0,   -- Gesamtspielzeit in Minuten
    login_count INTEGER DEFAULT 0   -- Anzahl der Logins
)
```

## 🛠️ Datenbank-Management

### Informationen anzeigen
```bash
python reset_database.py --info
```
Zeigt:
- Datenbankgröße
- Anzahl der Spieler
- Neueste und älteste Aktivität

### Top-Spieler anzeigen
```bash
# Top 10 Spieler nach Spielzeit
python reset_database.py --top 10

# Top 20 Spieler
python reset_database.py --top 20
```

### Backup erstellen
```bash
python reset_database.py --backup
```
Erstellt ein Backup: `db/players.db.backup_YYYYMMDD_HHMMSS`

### Datenbank optimieren
```bash
python reset_database.py --vacuum
```
Optimiert die Datenbankdatei und gibt ungenutzten Speicherplatz frei.

### Datenbank zurücksetzen (⚠️ ACHTUNG!)
```bash
python reset_database.py --reset
```
**WARNUNG**: Löscht alle Daten! Erstellt automatisch ein Backup vor dem Löschen.

## 📈 Aktuelle Statistiken

**Stand**: 4. Juli 2025
- **Spieler gesamt**: 336
- **Größe**: 48 KB
- **Neueste Aktivität**: KingBBQ42 (4. Juli 2025)
- **Älteste Aktivität**: <KingBBQ42> (31. August 2024)

## 🔍 Manuelle SQL-Abfragen

### Alle Spieler anzeigen
```bash
sqlite3 db/players.db "SELECT * FROM players ORDER BY total_time DESC LIMIT 10;"
```

### Spieler mit mehr als 100 Logins
```bash
sqlite3 db/players.db "SELECT username, login_count, total_time FROM players WHERE login_count > 100 ORDER BY login_count DESC;"
```

### Inaktive Spieler (180+ Tage)
```bash
sqlite3 db/players.db "SELECT username, last_login FROM players WHERE last_login < datetime('now', '-180 days') ORDER BY last_login ASC;"
```

### Anzahl Spieler pro Monat
```bash
sqlite3 db/players.db "SELECT strftime('%Y-%m', last_login) as month, COUNT(*) FROM players WHERE last_login IS NOT NULL GROUP BY month ORDER BY month DESC;"
```

## 🔄 Datenbank neu aufbauen

Falls die Datenbank neu aufgebaut werden soll:

### Option 1: Kompletter Reset (mit Backup)
```bash
# 1. Backup erstellen
python reset_database.py --backup

# 2. Datenbank zurücksetzen
python reset_database.py --reset

# 3. Agent starten (füllt Datenbank neu)
./start_agent.sh
```

### Option 2: Manuell löschen
```bash
# 1. Agent stoppen
./stop_agent.sh

# 2. Datenbank manuell löschen
rm db/players.db

# 3. Agent starten (erstellt neue Datenbank)
./start_agent.sh
```

### Option 3: Backup wiederherstellen
```bash
# 1. Verfügbare Backups anzeigen
ls -lh db/*.backup_*

# 2. Backup wiederherstellen
cp db/players.db.backup_20250704_153000 db/players.db
```

## 📝 Hinweise

- Die Datenbank wird **lokal** gespeichert und ist **nicht** auf dem Server
- Der Agent **muss laufen**, um die Datenbank zu aktualisieren
- Die Datenbank wird nur durch Login/Logout-Events im Minecraft-Log aktualisiert
- Bei Serverneustarts ohne Login/Logout-Events ändert sich die Datenbank nicht
- Backups sollten regelmäßig erstellt werden, besonders vor größeren Änderungen

## 🔗 Verwandte Scripts

- **main.py**: Agent, der die Datenbank automatisch aktualisiert
- **database.py**: Datenbank-Funktionen (CRUD-Operationen)
- **inactive_players_cleanup_with_chunks.py**: Nutzt die Datenbank für Cleanup-Operationen
- **reset_database.py**: Datenbank-Management-Tool