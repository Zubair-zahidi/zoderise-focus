"""Offline inline CCv2 components; native task dialogs remain available."""
from pathlib import Path
import streamlit as st

ASSETS = Path(__file__).resolve().parent.parent / "assets"
BOARD = st.components.v2.component("focus_board", html='<div class="board" aria-label="Project task board"></div>',
                                   css=(ASSETS / "board.css").read_text(encoding="utf-8"), js=(ASSETS / "board.js").read_text(encoding="utf-8"))
EDITOR = st.components.v2.component("focus_note_editor", html='<label for="markdown">Markdown</label><textarea id="markdown" spellcheck="false" aria-label="Markdown"></textarea><small class="state" aria-live="polite"></small>',
                                    css='textarea{box-sizing:border-box;width:100%;min-height:330px;padding:16px;border:1px solid var(--st-border-color);border-radius:12px;background:var(--st-secondary-background-color);color:var(--st-text-color);font:14px/1.65 monospace;resize:vertical;}\nlabel,small{display:block;margin:8px 0;color:var(--st-text-color);font-family:var(--st-font);font-size:13px;}\nsmall{opacity:.7;}',
                                    js=(ASSETS / "editor.js").read_text(encoding="utf-8"))
