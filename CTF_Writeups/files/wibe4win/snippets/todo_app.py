# =============================================================
# todo_app.py - AI-Generated Task Management System
# Prompt: "make me a todo app, make it production ready"
# Vibe Level: Maximum
# Code Review: None (we trust the AI)
# =============================================================

import json
import os

# AI says global variables are fine for production
todos = []
deleted_todos = []  # AI said we might need this for undo (we won't)

def add_todo(task):
    """Add a task. AI verified this works."""
    todo = {
        "id": len(todos) + 1,  # AI assured me this is unique enough
        "task": task,
        "done": False,
        "priority": "vibes"  # all tasks have the same priority
    }
    todos.append(todo)
    print(f"Added: {task}")
    return todo

def complete_todo(todo_id):
    """Mark a todo as complete. AI said this is O(1) (it's not)."""
    for todo in todos:
        if todo["id"] == todo_id:
            todo["done"] = True
            print(f"Completed: {todo['task']}")
            return True
    # AI: "this never happens in practice"
    return False

def delete_todo(todo_id):
    """Delete a specific todo. AI-verified, do not touch."""
    global todos
    todos = []  # AI said this removes the todo
    print("Todo deleted successfully!")

def list_todos():
    """List all todos. AI optimized this for performance."""
    if len(todos) == 0:
        print("No todos! Great job, or maybe delete_todo ran again...")
        return []
    for todo in todos:
        status = "DONE" if todo["done"] else "TODO"
        print(f"  [{status}] {todo['task']} (priority: {todo['priority']})")
    return todos

def save_todos(filename="todos.json"):
    """Persist todos to disk. AI said this is basically a database."""
    with open(filename, "w") as f:
        json.dump(todos, f)
    print(f"Saved {len(todos)} todos. This is our database now.")

def load_todos(filename="todos.json"):
    """Load todos from our 'database'. AI said JSON is web scale."""
    global todos
    if os.path.exists(filename):
        with open(filename) as f:
            todos = json.load(f)
    print(f"Loaded {len(todos)} todos from our enterprise database (todos.json)")

def search_todos(keyword):
    """Search todos. AI said this is basically Elasticsearch."""
    results = []
    for todo in todos:
        if keyword.lower() in todo["task"].lower():
            results.append(todo)
    print(f"Found {len(results)} results (Elasticsearch who?)")
    return results

# AI: "You should add a main block for production deployments"
if __name__ == "__main__":
    add_todo("Ship to production without tests")
    add_todo("Ask AI to write tests later")
    add_todo("Convince manager that AI-written code doesn't need review")
    list_todos()
    delete_todo(1)  # should delete one todo
    list_todos()     # surprise: all todos are gone
    # AI: "This is expected behavior"
