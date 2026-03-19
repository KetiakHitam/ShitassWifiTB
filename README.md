# ShitassWifiTB

A modular, multi-threaded Windows diagnostic utility designed for real-time network troubleshooting and latency analysis. Tinkered around with Antigravity during this too, made out of spite due to lagging at night

## Features

- **Dashboard**: Basic diagnostics (Ping, Gateway, DNS, Channel, Speedtest).
- **Logs**: Interactive `matplotlib` visualization querying a local SQLite database (`data/logs.db`) populated by a 24/7 background `Night Logger`. Incorporates a `Disconnect Monitor` that logs precise Windows interface connection state changes.
- **Deep Scan**: Queries Windows WMI and Registry variables to audit network interface configurations including Power Management, Roaming Aggressiveness, TCP Auto-Tuning, Nagle's Algorithm, and driver date.
- **Bandwidth Checks**: Associates active TCP/UDP sockets with local PIDs to identify background applications holding active network connections.
- **Game Mode**: High-frequency ICMP latency polling rendered to a rolling `matplotlib` timeline. Automatically highlights bounds exceeding standard latency thresholds.
- **Traceroute**: Asynchronous hop-by-hop latency mapping. Includes heuristic parsing to isolate fault origination between the local router architecture, ISP gateway nodes, or target servers.
- **Packet Analyzer**: Extracts loss indices from the Game Mode history buffer to classify latency drop signatures mathematically (Burst, Periodic, Random). Secondary module utilizes `scapy` to capture raw 802.11 Deauthentication frames on supported hardware (requires Npcap).

## Architecture

- **Frontend**: Structured via `customtkinter` classes decoupled in the `tabs/` directory. Applies a Discord dark-mode color palette (`#313338`, `#2b2d31`) with Catppuccin accenting.
- **Backend Engines**: Data collation and API/subprocess polling occur in independent Python threads managed in the `engines/` directory to prevent UI blocking.
- **Data Persistence**: Local `sqlite3` database initialization (`init_db.py`).

Note: Specific deep scan features and scapy sniffing require execution with Administrator privileges.
