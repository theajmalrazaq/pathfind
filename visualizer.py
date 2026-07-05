import tkinter as tk
from tkinter import ttk, messagebox
import random, time, heapq, math
from collections import deque

class finpath:
    def __init__(self, root):
        self.root = root
        self.root.title("Pathfind Visualizer")
        self.root.geometry("900x650")
        
        # Grid configuration
        self.rows, self.cols = 20, 30
        self.startpos, self.goalpos = (5, 5), (15, 25)
        self.grid = [['empty' for _ in range(100)] for _ in range(80)]
        self.running = False
        self.cancelled = False
        self.tool = tk.StringVar(value="wall")
        
        self.frontier, self.visited, self.pathnodes = set(), set(), []
        self.expanded, self.cost, self.exectime = 0, 0, 0.0
        
        self.colors = {
            'empty': '#FFFFFF', 'wall': '#334155', 'start': '#F97316', 'goal': '#8B5CF6',
            'frontier': '#FBBF24', 'visited': '#60A5FA', 'path': '#10B981', 'line': '#E2E8F0'
        }
        
        self.setup_ui()
        self.reset()

    def setup_ui(self):
        ctrl = tk.Frame(self.root, bg="#1E293B", pady=10)
        ctrl.pack(fill="x")
        
        row1 = tk.Frame(ctrl, bg="#1E293B")
        row1.pack(fill="x", padx=10)
        
        tk.Label(row1, text="Algorithm:", fg="white", bg="#1E293B").pack(side="left")
        self.algo = tk.StringVar(value="A* Search")
        self.algocb = ttk.Combobox(row1, textvariable=self.algo, state="readonly", width=12,
                                   values=["BFS", "UCS", "GBFS", "A* Search"])
        self.algocb.pack(side="left", padx=5)
        self.algocb.bind("<<ComboboxSelected>>", self.on_algo_change)
        
        tk.Label(row1, text="Heuristic:", fg="white", bg="#1E293B").pack(side="left", padx=(10, 0))
        self.heur = tk.StringVar(value="Manhattan")
        self.heurcb = ttk.Combobox(row1, textvariable=self.heur, state="readonly", width=10,
                                   values=["Manhattan", "Euclidean"])
        self.heurcb.pack(side="left", padx=5)
        
        tk.Label(row1, text="Rows:", fg="white", bg="#1E293B").pack(side="left", padx=(10, 0))
        self.rowsvar = tk.IntVar(value=self.rows)
        self.rowsspin = tk.Spinbox(row1, from_=5, to=80, textvariable=self.rowsvar, width=4, command=self.resize)
        self.rowsspin.pack(side="left", padx=5)
        
        tk.Label(row1, text="Cols:", fg="white", bg="#1E293B").pack(side="left", padx=(10, 0))
        self.colsvar = tk.IntVar(value=self.cols)
        self.colsspin = tk.Spinbox(row1, from_=5, to=100, textvariable=self.colsvar, width=4, command=self.resize)
        self.colsspin.pack(side="left", padx=5)
        
        tk.Label(row1, text="Density (%):", fg="white", bg="#1E293B").pack(side="left", padx=(10, 0))
        self.density = tk.IntVar(value=30)
        tk.Scale(row1, from_=10, to=60, variable=self.density, orient="horizontal", showvalue=False, width=10, bg="#1E293B").pack(side="left", padx=5)
        
        tk.Button(row1, text="Generate Maze", command=self.genmaze, bg="#3B82F6", fg="white", font=("Inter", 9, "bold")).pack(side="left", padx=10)
        
        row2 = tk.Frame(ctrl, bg="#1E293B", pady=5)
        row2.pack(fill="x", padx=10)
        
        for tname, val in [("Wall", "wall"), ("Erase", "erase"), ("Start", "start"), ("Goal", "goal")]:
            tk.Radiobutton(row2, text=tname, variable=self.tool, value=val, bg="#1E293B", fg="white", selectcolor="#0F172A").pack(side="left", padx=5)
            
        tk.Label(row2, text="Speed:", fg="white", bg="#1E293B").pack(side="left", padx=(10, 0))
        self.speed = tk.DoubleVar(value=0.01)
        tk.Scale(row2, from_=0.0, to=0.1, resolution=0.01, variable=self.speed, orient="horizontal", showvalue=False, width=10, bg="#1E293B").pack(side="left", padx=5)
        
        self.startbtn = tk.Button(row2, text="Run Search", command=self.fndpath, bg="#10B981", fg="white", font=("Inter", 9, "bold"))
        self.startbtn.pack(side="left", padx=10)
        
        self.resetbtn = tk.Button(row2, text="Reset Grid", command=self.reset, bg="#EF4444", fg="white", font=("Inter", 9, "bold"))
        self.resetbtn.pack(side="left", padx=5)
        
        self.metricslbl = tk.Label(row2, text="Expanded: 0 | Cost: 0 | Time: 0.0 ms", fg="#60A5FA", bg="#1E293B", font=("Inter", 10, "bold"))
        self.metricslbl.pack(side="right", padx=10)
        
        self.canvas = tk.Canvas(self.root, bg="#FFFFFF", highlightthickness=0)
        self.canvas.pack(fill="both", expand=True)
        self.canvas.bind("<Configure>", lambda e: self.draw())
        self.canvas.bind("<Button-1>", self.on_click)
        self.canvas.bind("<B1-Motion>", self.on_click)

    def reset(self):
        if self.running:
            self.cancelled = True
        for r in range(self.rows):
            for c in range(self.cols):
                self.grid[r][c] = 'empty'
        self.grid[self.startpos[0]][self.startpos[1]] = 'start'
        self.grid[self.goalpos[0]][self.goalpos[1]] = 'goal'
        self.clear()

    def clear(self):
        self.frontier.clear()
        self.visited.clear()
        self.pathnodes.clear()
        self.expanded, self.cost, self.exectime = 0, 0, 0.0
        self.updmetrics()
        self.draw()
        
    def resize(self):
        if self.running: return
        self.rows = min(80, max(5, self.rowsvar.get()))
        self.cols = min(100, max(5, self.colsvar.get()))
        self.startpos = (min(self.startpos[0], self.rows-1), min(self.startpos[1], self.cols-1))
        self.goalpos = (min(self.goalpos[0], self.rows-1), min(self.goalpos[1], self.cols-1))
        self.reset()

    def draw(self):
        self.canvas.delete("all")
        w, h = self.canvas.winfo_width(), self.canvas.winfo_height()
        if w <= 1 or h <= 1: return
        
        self.cellsize = min(w / self.cols, h / self.rows)
        self.ox, self.oy = (w - self.cellsize * self.cols)/2, (h - self.cellsize * self.rows)/2
        
        for r in range(self.rows):
            for c in range(self.cols):
                x1, y1 = self.ox + c * self.cellsize, self.oy + r * self.cellsize
                x2, y2 = x1 + self.cellsize, y1 + self.cellsize
                
                pos, state = (r, c), self.grid[r][c]
                color = self.colors['empty']
                label = ""
                
                if state == 'start': color, label = self.colors['start'], "S"
                elif state == 'goal': color, label = self.colors['goal'], "G"
                elif state == 'wall': color = self.colors['wall']
                elif pos in self.pathnodes: color = self.colors['path']
                elif pos in self.visited: color = self.colors['visited']
                elif pos in self.frontier: color = self.colors['frontier']
                
                self.canvas.create_rectangle(x1, y1, x2, y2, fill=color, outline=self.colors['line'])
                if label:
                    self.canvas.create_text(x1 + self.cellsize/2, y1 + self.cellsize/2, text=label,
                                            fill="white", font=("Inter", int(self.cellsize*0.6), "bold"))

    def on_click(self, event):
        if self.running: return
        c, r = int((event.x - self.ox) // self.cellsize), int((event.y - self.oy) // self.cellsize)
        if not (0 <= r < self.rows and 0 <= c < self.cols): return
        
        t = self.tool.get()
        if t == "start" and self.grid[r][c] != 'goal':
            self.grid[self.startpos[0]][self.startpos[1]] = 'empty'
            self.startpos = (r, c)
            self.grid[r][c] = 'start'
        elif t == "goal" and self.grid[r][c] != 'start':
            self.grid[self.goalpos[0]][self.goalpos[1]] = 'empty'
            self.goalpos = (r, c)
            self.grid[r][c] = 'goal'
        elif t == "wall" and self.grid[r][c] == 'empty':
            self.grid[r][c] = 'wall'
        elif t == "erase" and self.grid[r][c] == 'wall':
            self.grid[r][c] = 'empty'
        self.clear()

    def genmaze(self):
        if self.running: return
        self.clear()
        d = self.density.get() / 100.0
        for r in range(self.rows):
            for c in range(self.cols):
                if (r, c) not in [self.startpos, self.goalpos]:
                    self.grid[r][c] = 'wall' if random.random() < d else 'empty'
        self.draw()

    def on_algo_change(self, event=None):
        self.heurcb.configure(state="disabled" if self.algo.get() in ["BFS", "UCS"] else "readonly")

    def updmetrics(self):
        self.metricslbl.configure(text=f"Expanded: {self.expanded} | Cost: {self.cost} | Time: {self.exectime:.1f} ms")

    def fndpath(self):
        if self.running: return
        self.running, self.cancelled = True, False
        self.clear()
        
        a, hname = self.algo.get(), self.heur.get()
        use_fifo = a == "BFS"
        use_cost = a in ["UCS", "A* Search"]
        use_heur = a in ["GBFS", "A* Search"]
        
        starttime = time.perf_counter()
        
        if use_fifo:
            queue = deque([self.startpos])
        else:
            unique_id = 0
            frontier = [(0, unique_id, 0, self.startpos)]
            
        parent = {self.startpos: None}
        gscore = {self.startpos: 0}
        closed = set()
        self.frontier.add(self.startpos)
        
        while (use_fifo and queue) or (not use_fifo and frontier):
            if self.cancelled: break
            
            if use_fifo:
                current = queue.popleft()
            else:
                _, _, g, current = heapq.heappop(frontier)
                if current in closed: continue
                closed.add(current)
                
            self.frontier.discard(current)
            
            if current == self.goalpos:
                path = []
                curr = self.goalpos
                while curr in parent and parent[curr] is not None:
                    path.append(curr)
                    curr = parent[curr]
                path.reverse()
                if path and path[-1] == self.goalpos: path.pop()
                self.pathnodes = path
                self.cost = len(path) + 1
                self.exectime = (time.perf_counter() - starttime) * 1000.0
                break
                
            if current != self.startpos:
                self.visited.add(current)
                self.expanded += 1
                
            self.exectime = (time.perf_counter() - starttime) * 1000.0
            self.updmetrics()
            self.draw()
            self.root.update()
            
            s = self.speed.get()
            if s > 0: time.sleep(s)
            
            r, c = current
            for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                nr, nc = r + dr, c + dc
                if 0 <= nr < self.rows and 0 <= nc < self.cols and self.grid[nr][nc] != 'wall':
                    neighbor = (nr, nc)
                    if use_fifo:
                        if neighbor not in parent:
                            parent[neighbor] = current
                            queue.append(neighbor)
                            self.frontier.add(neighbor)
                    else:
                        new_g = gscore[current] + 1
                        if new_g < gscore.get(neighbor, float('inf')):
                            gscore[neighbor] = new_g
                            parent[neighbor] = current
                            self.frontier.add(neighbor)
                            
                            h = abs(nr - self.goalpos[0]) + abs(nc - self.goalpos[1]) if hname == "Manhattan" else math.sqrt((nr - self.goalpos[0])**2 + (nc - self.goalpos[1])**2)
                            h = h if use_heur else 0
                            f = (new_g + h) if (use_cost and use_heur) else (h if use_heur else new_g)
                            
                            unique_id += 1
                            heapq.heappush(frontier, (f, unique_id, new_g, neighbor))
                            
        self.updmetrics()
        self.draw()
        self.running = False

if __name__ == "__main__":
    root = tk.Tk()
    app = finpath(root)
    root.mainloop()
