# 🧠 Graph Theory Visualizer

An intuitive, interactive tool for building, analyzing, and visualizing graphs and NP-complete problems — built with **Python** and **Pygame**.

🛠️ Developed by **dannythedev**  
🔓 License: Free to use for personal and academic usage.

---

## ✨ Features at a Glance

- 🧱 **Graph Construction** (vertices, edges, labels)
- 🔁 **Directed / Undirected Toggle**
- 💾 **Save / Load** to JSON
- 🧩 **Live NP Problem Solvers**
- 📊 **Real-time Graph Diagnostics**
- 🔍 **Smart Highlighting and Color Grouping**
- 🖱️ **Fully Mouse-Controlled UI**
- ⚡ **Zoom & Pan Support**

---

## 🖱️ Mouse + UI Controls

| Action | How to Do It |
|--------|--------------|
| ➕ Add Vertex | Left-click on empty space |
| 🔗 Connect Vertices | Left-click two vertices |
| ✏️ Edit Label | Double-click on a vertex or edge |
| ✖️️ Delete | Right-click a vertex or edge |
| 🧲 Move Vertex | Drag with mouse |
| 🎯 Toggle Directed Mode | Click "Directed: ON/OFF" |
| 📈 Change `k` | Click `k=` box and type |
| 💾 Save / Load / Clear | Use on-screen buttons |
| 🔍 Zoom | Scroll mouse wheel |
| 📦 Duplicate Graph | Use Duplicate button + slider |

---

## 🧪 Real-Time Graph Diagnostics

These update whenever the graph changes:

| Metric | Meaning |
|--------|---------|
| **Cyclic** | Does the graph contain a cycle? |
| **Components** | Number of connected components |
| **SCCs** | Strongly Connected Components (if directed) |
| **Tree / Forest** | Is it a tree or forest? |
| **Bipartite** | Can it be split into two colorable sets? |
| **Bridges** | Critical edges whose removal disconnects components |
| **Max/Min Degree** | Nodes with highest/lowest degree |

Hovering over any diagnostic highlights relevant nodes or edges.

---

## 🧠 NP Problem Solvers

Live NP-complete problem checks with optional `k` input:

| Problem | Description | Needs `k`? |
|---------|-------------|------------|
| 🧮 **k-Coloring** | Color graph with ≤ k colors (undirected only) | ✅ |
| 🎯 **Vertex Cover** | Cover all edges using ≤ k vertices | ✅ |
| 🧩 **Clique** | Fully connected group of ≥ k nodes | ✅ |
| 🔍 **Independent Set** | ≥ k non-adjacent nodes | ✅ |
| 🧭 **Hamiltonian Path** | Visit all vertices exactly once | ❌ |
| 🔄 **Hamiltonian Cycle** | Visit all vertices once and return | ❌ |
| 🔓 **Min-Cut** | Disconnect graph by removing ≤ k nodes | ✅ |
| 📏 **Longest Path** | Find the longest simple path | ❌ |

**Coloring magic:**  
Hover over *k-Coloring* to highlight color groups with beautiful, contrast-aware shades that avoid clashing with the UI!

---

## 🧩 Architecture Overview

| File | Purpose |
|------|---------|
| `main.py` | UI loop, event handling, and rendering |
| `graph.py` | Graph structure, drawing, and interaction |
| `diagnostics.py` | Real-time graph metric calculations |
| `np_problems.py` | Solvers for classic NP-complete problems |
| `physics.py` | Graph layout physics (smooth dragging, nudging) |
| `math_text.py` | Render math-style labels (LaTeX-style) |
| `config.py` | Colors, fonts, and constants |
| `requirements.txt` | Dependency list |

---

## 🚀 Getting Started

### 📦 Prerequisites

- Python 3.7+
- `pygame` and `matplotlib`

### 📥 Installation

```bash
pip install -r requirements.txt
