#!/usr/bin/env python3
from __future__ import annotations
import argparse
import sys
from pathlib import Path
from pathlib import Path
import re
import os
import subprocess
import tempfile
from dataclasses import dataclass
from collections import defaultdict

APP_NAME = "world-builder"
DEFAULT_DATA_DIR = Path.home() / ".local" / "share" / "world_builder"

@dataclass
class Node:
    type: str
    parent: str  # "-" or path like /continents/edoras
    notes: str   # may be ""

def read_node(path: Path) -> Node:
    text = path.read_text(encoding="utf-8").splitlines()
    t = text[0].strip() if len(text) > 0 else "Node"
    parent = text[1].strip() if len(text) > 1 else "-"
    notes = "\n".join(text[2:]) if len(text) > 2 else ""
    return Node(type=t, parent=parent, notes=notes)

def iter_nodes(data_dir: Path):
    yield from sorted(data_dir.glob("*.txt"))

def build_index(data_dir: Path):
    # name->Node and parent->list(names)
    nodes = {}
    children = defaultdict(list)

    for path in iter_nodes(data_dir):
        name = path.stem
        n = read_node(path)
        nodes[name] = n
        parent = n.parent if n.parent and n.parent != "-" else None
        children[parent].append(name)

    # sort child lists
    for k in children:
        children[k].sort(key=str.lower)
    return nodes, children

def cmd_edit(args) -> int:
    data_dir = Path(args.dir).expanduser().resolve()
    path = node_path(data_dir, args.name)
    if not path.exists():
        print(f"Node not found: {path}")
        return 1

    editor = os.environ.get("EDITOR") or os.environ.get("VISUAL") or "nano"
    # Open the file directly so line endings/encoding stay intact
    try:
        subprocess.run([editor, str(path)], check=True)
    except FileNotFoundError:
        print(f"Editor not found: {editor}")
        return 1
    return 0
    
def cmd_list(args) -> int:
    data_dir = Path(args.dir).expanduser().resolve()
    if not data_dir.exists():
        print(f"No data directory: {data_dir}")
        return 1
    count = 0
    for path in iter_nodes(data_dir):
        n = read_node(path)
        if args.type and n.type.lower() != args.type.lower():
            continue
        name = path.stem
        print(f"{name:30}  [{n.type}]  parent={n.parent}")
        count += 1
    if count == 0:
        print("(no nodes)")
    return 0

def cmd_show(args) -> int:
    data_dir = Path(args.dir).expanduser().resolve()
    path = node_path(data_dir, args.name)
    if not path.exists():
        print(f"Node not found: {path}")
        return 1
    n = read_node(path)
    print(f"Name:   {args.name}")
    print(f"Type:   {n.type}")
    print(f"Parent: {n.parent}")
    print("Notes:")
    print(n.notes if n.notes else "(none)")
    return 0

def cmd_tree(args) -> int:
    data_dir = Path(args.dir).expanduser().resolve()
    if not data_dir.exists():
        print(f"No data directory: {data_dir}")
        return 1

    nodes, children = build_index(data_dir)

    def display(name: str, prefix: str = ""):
        n = nodes.get(name)
        label = f"{name} [{n.type}]" if n else name
        print(prefix + label)
        kids = children.get(f"/{name}", [])  # support absolute-style parents like "/continents/edoras"
        # Also support direct name parents (no leading slash)
        kids += children.get(name, [])
        # de-dup while preserving order
        seen = set()
        ordered = []
        for k in kids:
            if k not in seen:
                seen.add(k)
                ordered.append(k)
        for i, child in enumerate(ordered):
            last = i == len(ordered) - 1
            branch = "└─ " if last else "├─ "
            child_prefix = "   " if last else "│  "
            display(child, prefix + branch)
            # adjust prefix for grandchildren
            if children.get(child) or children.get(f"/{child}"):
                pass  # handled by recursive call

    # Roots: nodes with parent None or "-"
    roots = []
    for name, n in nodes.items():
        if not n.parent or n.parent == "-":
            roots.append(name)
    roots.sort(key=str.lower)

    if args.root:
        # Start from a specific root name
        start = args.root
        if start not in nodes:
            print(f"Root not found: {start}")
            return 1
        display(start)
    else:
        for r in roots:
            display(r)
            print()
    return 0

def cmd_init(args: argparse.Namespace) -> int:
    data_dir = Path(args.dir).expanduser().resolve()
    data_dir.mkdir(parents=True, exist_ok=True)
    readme = data_dir / "README.txt"
    if not readme.exists():
        readme.write_text(
            "World Builder data directory.\n"
            "You can store your notes here in plain text files.\n",
            encoding="utf-8",
        )
    print(f"Initialized data directory at: {data_dir}")
    return 0

def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog=APP_NAME, description="World Builder CLI"
    )
    parser.add_argument(
        "-v", "--version", action="version", version="0.1.0"
    )

    sub = parser.add_subparsers(dest="command", required=True)

    p_init = sub.add_parser(
        "init", help="initialize a data directory"
    )
    p_init.add_argument(
        "-d", "--dir",
        default=str(DEFAULT_DATA_DIR),
        help=f"directory for data (default: {DEFAULT_DATA_DIR})",
    )
    p_init.set_defaults(func=cmd_init)
    p_add = sub.add_parser("add", help="add a node")
    p_add.add_argument("name", help="node name")
    p_add.add_argument("-t", "--type", default="Node", help="node type (e.g., Continent, Kingdom)")
    p_add.add_argument("-p", "--parent", default=None, help="parent path (e.g., /continents/edoras) or '-'")
    p_add.add_argument("-n", "--notes", default="", help="initial notes")
    p_add.add_argument("-d", "--dir", default=str(DEFAULT_DATA_DIR), help="data dir")
    p_add.add_argument("-f", "--force", action="store_true", help="overwrite if exists")
    p_add.set_defaults(func=cmd_add)
    p_list = sub.add_parser("list", help="list nodes")
    p_list.add_argument("-t", "--type", default=None, help="filter by type (e.g., Kingdom)")
    p_list.add_argument("-d", "--dir", default=str(DEFAULT_DATA_DIR), help="data dir")
    p_list.set_defaults(func=cmd_list)

    p_show = sub.add_parser("show", help="show a node")
    p_show.add_argument("name", help="node name")
    p_show.add_argument("-d", "--dir", default=str(DEFAULT_DATA_DIR), help="data dir")
    p_show.set_defaults(func=cmd_show)
    
    p_edit = sub.add_parser("edit", help="edit a node in $EDITOR")
    p_edit.add_argument("name", help="node name")
    p_edit.add_argument("-d", "--dir", default=str(DEFAULT_DATA_DIR), help="data dir")
    p_edit.set_defaults(func=cmd_edit)
    
    p_tree = sub.add_parser("tree", help="print hierarchy tree")
    p_tree.add_argument("-r", "--root", help="start from a specific root node name")
    p_tree.add_argument("-d", "--dir", default=str(DEFAULT_DATA_DIR), help="data dir")
    p_tree.set_defaults(func=cmd_tree)

    return parser

def slugify(name: str) -> str:
    s = name.lower().strip()
    s = re.sub(r"[^a-z0-9]+", "_", s)
    return re.sub(r"_+", "_", s).strip("_")

def node_path(data_dir: Path, name: str) -> Path:
    return data_dir / f"{slugify(name)}.txt"

def cmd_add(args) -> int:
    data_dir = Path(args.dir).expanduser().resolve()
    data_dir.mkdir(parents=True, exist_ok=True)

    path = node_path(data_dir, args.name)
    if path.exists() and not args.force:
        print(f"Refusing to overwrite existing node: {path}")
        return 1

    parent = args.parent or "-"
    lines = [args.type, parent]
    if args.notes:
        lines.append(args.notes)

    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"Created node: {path}")
    return 0

def main(argv: list[str] | None = None) -> int:
    argv = argv if argv is not None else sys.argv[1:]
    parser = build_parser()
    args = parser.parse_args(argv)
    return args.func(args)

if __name__ == "__main__":
    raise SystemExit(main())