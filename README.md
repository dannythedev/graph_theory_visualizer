# Graph Theory Visualizer

A powerful interactive tool for building, analyzing, and visualizing graphs and NP-complete problems. Built using Python and Pygame, it supports intuitive mouse-driven graph construction and live updates of graph-theoretic diagnostics and problem-solving visualizations.

---

## 🎯 Features
![image](https://github.com/user-attachments/assets/27e9c894-9eb3-408d-a8ab-4ab9f1609fe5)

### 🧱 Graph Construction
- **Add Vertices**: Left-click on empty space.
- **Connect Vertices**: Click two vertices to create an edge.
- **Delete Vertices/Edges**: Double-click on them.
- **Rename Vertices / Label Edges**: Right-click to enter edit mode.
- **Move Vertices**: Drag them with the mouse.
- **Directed / Undirected Toggle**: Switch between graph modes.

### 💾 Graph I/O
- **Save Graph**: Persist graph to a JSON file.
- **Load Graph**: Load previously saved graphs.
- **Clear Graph**: Remove all vertices and edges.

---

## 🧠 NP Problem Solvers

These solvers run in the background and show live analysis based on the current graph:

| Problem Name          | Description                                              | Uses `k`? |
|-----------------------|----------------------------------------------------------|-----------|
| **Independent Set**   | Is there a set of ≥ k non-adjacent vertices?             | ✅         |
| **Clique**            | Is there a set of ≥ k mutually connected vertices?       | ✅         |
| **Vertex Cover**      | Can all edges be covered by ≤ k vertices?                | ✅         |
| **Hamiltonian Path**  | Is there a path that visits every vertex exactly once?   | ❌         |
| **k-Coloring**        | Can the graph be colored with ≤ k colors? _(Undirected only)_ | ✅    |

Each solver:
- Shows a result (`True`, `False`, or `Computing...`)
- Displays the set of vertices (or color groups) if applicable
- Is updated dynamically when the graph or `k` changes

#### 🎨 Special Feature:
Hovering over the **k-COLORING** line:
- Highlights color groups in visually distinct, non-overlapping colors
- Automatically avoids colors too similar to UI highlights

---

## 🧪 Graph Diagnostics

Continuously updated (but efficiently computed) facts about the current graph:

| Metric                        | Description                                               |
|-------------------------------|-----------------------------------------------------------|
| **Cyclic**                    | Whether the graph contains any cycles                    |
| **Components**                | Number of connected components (undirected)              |
| **Strongly Connected Components** | Number of strongly connected components (directed graphs) |

Diagnostics are rendered near the bottom of the screen and only recomputed when the graph changes.

---

## 🖱️ Controls

| Action                     | Mouse/Keyboard                             |
|----------------------------|--------------------------------------------|
| Add Vertex                 | Left-click on empty space                  |
| Select/Connect Vertices   | Left-click two vertices                    |
| Move Vertex               | Drag with left mouse button                |
| Delete Vertex/Edge        | Double-click on it                         |
| Edit Vertex/Edge Label    | Right-click                                |
| Toggle Directed Mode      | Click "Directed: ON/OFF"                   |
| Change `k`                | Click `k:` box and type number             |
| Save/Load/Clear Graph     | Use on-screen buttons                      |

---

## 🛠️ Code Structure

| File            | Purpose                                      |
|-----------------|----------------------------------------------|
| `main.py`       | Main UI loop and user interaction            |
| `graph.py`      | Vertex and Edge classes + rendering          |
| `np_problems.py`| NP problem solvers and abstraction           |
| `physics.py`    | Spring physics system for layout stability   |
| `diagnostics.py`| Graph diagnostic metrics (cycles, components)|
| `config.py`     | UI settings and global constants             |

---

## 🧩 Design Highlights

- ⚡ **Efficient updates**: Diagnostics and problem solvers only recalculate when the graph changes.
- 🧠 **Pluggable problem solvers**: Easily extendable via subclassing `NPProblem`.
- 🎨 **Smart coloring**: k-COLORING uses HSV + contrast filtering to avoid UI clashes.
- 👁️ **Intuitive interface**: Fully mouse-driven, no arcane commands needed.
- 🧪 **Live feedback**: Problems update as you edit the graph in real time.

---

## 🚧 Limitations

- Not optimized for very large graphs (>22 vertices).
- NP solvers use brute-force and are slow for large `k`.
- k-COLORING is disabled when graph is directed.

---

## 📦 Requirements

- Python 3.7+
- `pygame` library

```bash
pip install pygame
