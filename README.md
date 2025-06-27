# 🧠 Graph Theory Visualizer

An intuitive, interactive tool for building, analyzing, and visualizing graphs and NP-complete problems — built with **Python** and **Pygame**.

🛠️ Developed by **dannythedev**  
🔓 License: Free to use for personal and academic usage.

---

## ✨ Features at a Glance

- 🧱 **Graph Construction** (vertices, edges, labels)
- 🔁 **Directed / Undirected Toggle**
- 💾 **Save / Load / Clear / Duplicate / Random**
- 🧩 **Live NP Problem Solvers**
- ⚙️ **Graph Algorithm Simulations**
- 📊 **Real-time Graph Diagnostics**
- 🔍 **Smart Highlighting and Color Grouping**
- 🖱️ **Fully Mouse-Controlled UI**
- ⚡ **Zoom & Pan Support**

---

## 🖱️ Mouse + UI Controls

| Action            | How to Do It                                                                                        |
|-------------------|-----------------------------------------------------------------------------------------------------|
| ➕ Add Vertex      | Left-click on empty space.                                                                          |
| 🔗 Connect Vertices | Left-click two vertices.                                                                            |
| ✏️ Edit Label     | Double-click a vertex or edge.                                                                      |
| ✖️ Delete         | Right-click a vertex or edge.                                                                       |
| 🧲 Move Vertex    | Right-click and drag to move one vertex.<br/>Scroll-click and drag to move its connected group.     |
| 🎯 Select S/T     | Click "Select S/T" and then two vertices<br/>to activate [🔍 Graph Algorithms](#-graph-algorithms). |
| 📈 Change `k`     | Click `k=` box and type the k-value to<br/>activate [🧠 NP Problem Solvers](#-np-problem-solvers).  |
| 💾 Save / Load / Clear | Use respective buttons to Export/Import/Clear<br/>the current Graph.                                |
| 📦 Duplicate Graph | Use "Duplicate" button + slider to control<br/>the amount of duplications.                          |
| 🎲 Generate Random Graph | Click "Random" button.                                                                              |
| 🔍 Zoom           | Scroll mouse wheel.                                                                                 |

---

## ❗Hovering over a [🧪 Real-Time Graph Diagnostics](#-real-time-graph-diagnostics),[🔍 Graph Algorithms](#-graph-algorithms) or [🧠 NP Problem Solvers](#-np-problem-solvers) highlights relevant nodes or edges.


---

## 🧪 Real-Time Graph Diagnostics

These update automatically when the graph changes:

| Metric | Meaning |
|--------|---------|
| **Cyclic** | Does the graph contain a cycle? |
| **Components** | Number of connected components |
| **SCCs** | Strongly Connected Components (if directed) |
| **Tree / Forest** | Is it a tree or forest? |
| **Bipartite** | Can it be split into two colorable sets? |
| **Bridges** | Critical edges whose removal disconnects components |
| **Max/Min Degree** | Nodes with highest/lowest degree |

---

## 🔍 Graph Algorithms

| Algorithm                 | Description |
|---------------------------|-------------|
| **Dijkstra’s Algorithm**  | Shortest path from a source using non-negative weights |
| **Bellman-Ford Algorithm** | Shortest path that supports negative edge weights |
| **A***                    | Intelligent shortest pathfinding using heuristics (Euclidean by default) |
| **Prim’s Algorithm**      | Minimum Spanning Tree (MST) covering each connected component |
| **Kruskal’s Algorithm**   | MST using greedy edge inclusion across components |

**Note**:  
- Algorithms requiring a source/target (Dijkstra, Bellman-Ford, A\*) prompt for S/T selection.  
- Prim and Kruskal run automatically for all components — no S/T selection needed.  

---

## 🧠 NP Problem Solvers

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
| `main.py` | UI loop, event handling, rendering |
| `graph.py` | Graph structure and drawing |
| `diagnostics.py` | Real-time graph metrics |
| `np_problems.py` | Classic NP problem solvers |
| `algorithms.py` | Pathfinding and MST algorithms |
| `physics.py` | Dragging and layout physics |
| `math_text.py` | Renders math-style labels |
| `zoom_manager.py` | Pan and zoom support |
| `config.py` | Colors, fonts, constants |
| `utils.py` | Helper functions |
| `requirements.txt` | Dependency list |

---

## ⚠️ Note

This tool is designed for learning and visuality. While many classic algorithms and NP solvers are included, some results may be imperfect or suboptimal. This project was built for fun.
Great for insight — not guaranteed for proof.


---

## 🚀 Getting Started

### 📦 Prerequisites

- Python 3.7+
- `pygame`, `matplotlib`

### 📥 Installation

```bash
pip install -r requirements.txt
