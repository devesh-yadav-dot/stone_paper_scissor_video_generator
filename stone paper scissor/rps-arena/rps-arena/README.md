# 🪨📄✂️ Rock Paper Scissors AI Arena

A real-time simulation where autonomous agents battle each other using Rock-Paper-Scissors rules — built with Python and Pygame.

![Python](https://img.shields.io/badge/Python-3.8%2B-blue?logo=python)
![Pygame](https://img.shields.io/badge/Pygame-2.x-green?logo=pygame)
![License](https://img.shields.io/badge/License-MIT-yellow)

---

## 📺 Demo

Hundreds of agents (Rock 🪨, Paper 📄, Scissors ✂️) bounce around an arena and convert each other on contact. The last type standing wins — then a new round begins automatically.

---

## ✨ Features

- **Autonomous agents** — each entity moves independently with randomized velocity and bounces off walls
- **RPS conversion rules** — when two opposing agents collide, the loser converts to the winner's type
- **Balance & Survival mechanics** — outnumbered teams receive a speed boost; critically low teams enter **Survival Mode** with smart AI (flee predators, chase prey)
- **Particle effects** — explosion bursts on every conversion
- **Live scoreboard** — real-time counts, win history, and match streaks
- **Background music** — plays `bg.mp3` if present in the directory (toggle with `M`)
- **Sound effects** *(bot2 only)* — conversion beeps and win jingles (loads `change.mp3` / `win.mp3` or generates fallback beeps)
- **Auto-restart** — new match begins automatically after a winner is declared

---

## 🗂️ Project Structure

```
rps-arena/
├── bot.py           # Version 1 — ZoldaAI Arena (polished UI, animated watermark, background music)
├── bot2.py          # Version 2 — Minimal dark theme, grid counters, sound effects
├── assets/
│   ├── rock.png     # Rock agent sprite
│   ├── paper.png    # Paper agent sprite
│   └── scissors.png # Scissors agent sprite
├── requirements.txt
├── .gitignore
└── README.md
```

> **Note:** Place `rock.png`, `paper.png`, and `scissors.png` in the same directory as the script you run. If images are missing, colored circle fallbacks are used automatically.

---

## 🚀 Getting Started

### Prerequisites

- Python 3.8+
- pip

### Installation

```bash
# Clone the repository
git clone https://github.com/your-username/rps-arena.git
cd rps-arena

# Install dependencies
pip install -r requirements.txt
```

### Running

```bash
# Run the polished version (bot.py — ZoldaAI Arena)
python bot.py

# Run the minimal dark-theme version (bot2.py)
python bot2.py
```

### Optional Assets

| File | Description |
|------|-------------|
| `rock.png` / `paper.png` / `scissors.png` | Agent sprites (28×28 px recommended) |
| `bg.mp3` | Background music (bot.py only) |
| `change.mp3` | Conversion sound effect (bot2.py) |
| `win.mp3` | Victory sound effect (bot2.py) |

All assets are optional — the simulation runs without them using built-in fallbacks.

---

## 🎮 Controls

| Key | Action |
|-----|--------|
| `SPACE` | Pause / Resume |
| `R` | Reset match |
| `M` | Toggle music *(bot.py only)* |
| `Q` / Close window | Quit |

---

## ⚙️ Configuration

Key constants at the top of each file you can tweak:

| Constant | Default | Description |
|----------|---------|-------------|
| `AGENTS_PER_TYPE` | `15` | Starting agents per team |
| `LOW_COUNT_THRESHOLD` | `5` | Threshold to trigger balance boost |
| `CRITICAL_COUNT_THRESHOLD` | `2` | Threshold to trigger survival mode |
| `BALANCE_FACTOR` | `0.3` | Speed multiplier for low teams |
| `SURVIVAL_FACTOR` | `0.6` | Additional speed boost in survival mode |
| `FPS` | `60` | Target frame rate |

---

## 🧠 How the AI Works

Agents use a simple priority-based decision system:

1. **Normal mode** — random wandering with occasional direction changes
2. **Low team mode** (`≤ 5 agents`) — increased speed and direction change frequency
3. **Survival mode** (`≤ 2 agents`) — smart behavior:
   - If a **predator** is within 150px → flee
   - Else if **prey** is within 200px → chase
   - Random jitter to avoid getting stuck

Collision detection uses a **spatial grid** for performance, checking only agents in the same or adjacent grid cells.

---

## 🆚 bot.py vs bot2.py

| Feature | bot.py | bot2.py |
|---------|--------|---------|
| Theme | Dark blue, modern UI | Pure black, terminal aesthetic |
| Watermark | Animated ZoldaAI logo | Static `@zolda Ai` diagonal text |
| Background music | ✅ (`bg.mp3`) | ❌ |
| Sound effects | ❌ | ✅ (beeps / custom files) |
| Win screen | Animated pulse + history | Simple text overlay |
| Caption bar | ❌ | ✅ (custom caption text) |
| Agent size | 28px | 24px |

---

## 📦 Requirements

```
pygame>=2.0.0
```

---

## 📄 License

MIT License — free to use, modify, and distribute.

---

## 🙏 Credits

Built by **ZoldaAI** — simulation inspired by the viral Rock Paper Scissors battle videos.
