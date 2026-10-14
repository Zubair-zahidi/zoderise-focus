"""One-time source migration: wrap native UI labels, preserving user data."""
import ast
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
COMMANDS = {"caption", "title", "subheader", "header", "write", "markdown", "text_input", "text_area", "button", "form_submit_button", "selectbox", "multiselect", "number_input", "date_input", "slider", "toggle", "checkbox", "download_button", "file_uploader", "expander", "popover", "info", "warning", "success", "error", "toast", "tabs"}

def translated(node):
    if isinstance(node, ast.Constant) and isinstance(node.value, str) and node.value:
        return ast.Call(func=ast.Name(id="t", ctx=ast.Load()), args=[node], keywords=[])
    if isinstance(node, ast.List):
        node.elts = [translated(item) for item in node.elts]
    return node

class Labels(ast.NodeTransformer):
    def visit_Call(self, node):
        self.generic_visit(node)
        if isinstance(node.func, ast.Attribute) and isinstance(node.func.value, ast.Name) and node.func.value.id == "st":
            if node.func.attr in COMMANDS and node.args:
                node.args[0] = translated(node.args[0])
            for kw in node.keywords:
                if kw.arg in ("label", "placeholder", "help") or node.func.attr == "Page" and kw.arg == "title":
                    kw.value = translated(kw.value)
        if isinstance(node.func, ast.Name) and node.func.id == "header":
            node.args = [translated(arg) for arg in node.args]
        return node

for path in [ROOT / "app.py", ROOT / "focus" / "ui.py", *sorted((ROOT / "app_pages").glob("*.py"))]:
    tree = Labels().visit(ast.parse(path.read_text(encoding="utf-8")))
    tree.body.insert(1 if path.name == "ui.py" else 0, ast.ImportFrom(module="focus.i18n", names=[ast.alias(name="t")], level=0))
    path.write_text(ast.unparse(ast.fix_missing_locations(tree)) + "\n", encoding="utf-8")
