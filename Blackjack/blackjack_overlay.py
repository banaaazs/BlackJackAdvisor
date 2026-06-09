#!/usr/bin/env python3
"""
Blackjack Strategy Overlay
===========================
Valós idejű képernyőfigyelő overlay.

TELEPÍTÉS:
  pip install pillow mss pytesseract numpy opencv-python tkinter

  Tesseract OCR szükséges:
    - macOS:   brew install tesseract
    - Ubuntu:  sudo apt install tesseract-ocr
    - Windows: https://github.com/UB-Mannheim/tesseract/wiki

HASZNÁLAT:
  python3 blackjack_overlay.py

VEZÉRLŐK:
  - Az overlay ablak mindig a többi felett marad
  - Manuális mód: kézzel add meg a lapokat a gombokkal
  - Auto mód: a program figyeli a képernyőt (Tesseract szükséges)
  - Esc / Q: kilépés
"""

import tkinter as tk
from tkinter import ttk, font
import sys
import threading
import time
import json
from typing import Optional, List, Tuple

# ── Strategy tables ────────────────────────────────────────────────────────────

HARD = {
    5:  {2:'H',3:'H',4:'H',5:'H',6:'H',7:'H',8:'H',9:'H',10:'H','A':'H'},
    6:  {2:'H',3:'H',4:'H',5:'H',6:'H',7:'H',8:'H',9:'H',10:'H','A':'H'},
    7:  {2:'H',3:'H',4:'H',5:'H',6:'H',7:'H',8:'H',9:'H',10:'H','A':'H'},
    8:  {2:'H',3:'H',4:'H',5:'H',6:'H',7:'H',8:'H',9:'H',10:'H','A':'H'},
    9:  {2:'H',3:'D',4:'D',5:'D',6:'D',7:'H',8:'H',9:'H',10:'H','A':'H'},
    10: {2:'D',3:'D',4:'D',5:'D',6:'D',7:'D',8:'D',9:'D',10:'H','A':'H'},
    11: {2:'D',3:'D',4:'D',5:'D',6:'D',7:'D',8:'D',9:'D',10:'D','A':'D'},
    12: {2:'H',3:'H',4:'S',5:'S',6:'S',7:'H',8:'H',9:'H',10:'H','A':'H'},
    13: {2:'S',3:'S',4:'S',5:'S',6:'S',7:'H',8:'H',9:'H',10:'H','A':'H'},
    14: {2:'S',3:'S',4:'S',5:'S',6:'S',7:'H',8:'H',9:'H',10:'H','A':'H'},
    15: {2:'S',3:'S',4:'S',5:'S',6:'S',7:'H',8:'H',9:'R',10:'R','A':'R'},
    16: {2:'S',3:'S',4:'S',5:'S',6:'S',7:'H',8:'R',9:'R',10:'R','A':'R'},
    17: {2:'S',3:'S',4:'S',5:'S',6:'S',7:'S',8:'S',9:'S',10:'S','A':'S'},
    18: {2:'S',3:'S',4:'S',5:'S',6:'S',7:'S',8:'S',9:'S',10:'S','A':'S'},
    19: {2:'S',3:'S',4:'S',5:'S',6:'S',7:'S',8:'S',9:'S',10:'S','A':'S'},
    20: {2:'S',3:'S',4:'S',5:'S',6:'S',7:'S',8:'S',9:'S',10:'S','A':'S'},
    21: {2:'S',3:'S',4:'S',5:'S',6:'S',7:'S',8:'S',9:'S',10:'S','A':'S'},
}

SOFT = {
    13: {2:'H',3:'H',4:'H',5:'D',6:'D',7:'H',8:'H',9:'H',10:'H','A':'H'},
    14: {2:'H',3:'H',4:'H',5:'D',6:'D',7:'H',8:'H',9:'H',10:'H','A':'H'},
    15: {2:'H',3:'H',4:'D',5:'D',6:'D',7:'H',8:'H',9:'H',10:'H','A':'H'},
    16: {2:'H',3:'H',4:'D',5:'D',6:'D',7:'H',8:'H',9:'H',10:'H','A':'H'},
    17: {2:'H',3:'D',4:'D',5:'D',6:'D',7:'H',8:'H',9:'H',10:'H','A':'H'},
    18: {2:'S',3:'D',4:'D',5:'D',6:'D',7:'S',8:'S',9:'H',10:'H','A':'H'},
    19: {2:'S',3:'S',4:'S',5:'S',6:'S',7:'S',8:'S',9:'S',10:'S','A':'S'},
    20: {2:'S',3:'S',4:'S',5:'S',6:'S',7:'S',8:'S',9:'S',10:'S','A':'S'},
}

PAIRS = {
    'A':  {2:'P',3:'P',4:'P',5:'P',6:'P',7:'P',8:'P',9:'P',10:'P','A':'P'},
    '10': {2:'S',3:'S',4:'S',5:'S',6:'S',7:'S',8:'S',9:'S',10:'S','A':'S'},
    '9':  {2:'P',3:'P',4:'P',5:'P',6:'P',7:'S',8:'P',9:'P',10:'S','A':'S'},
    '8':  {2:'P',3:'P',4:'P',5:'P',6:'P',7:'P',8:'P',9:'P',10:'P','A':'P'},
    '7':  {2:'P',3:'P',4:'P',5:'P',6:'P',7:'P',8:'H',9:'H',10:'H','A':'H'},
    '6':  {2:'P',3:'P',4:'P',5:'P',6:'P',7:'H',8:'H',9:'H',10:'H','A':'H'},
    '5':  {2:'D',3:'D',4:'D',5:'D',6:'D',7:'D',8:'D',9:'D',10:'H','A':'H'},
    '4':  {2:'H',3:'H',4:'H',5:'P',6:'P',7:'H',8:'H',9:'H',10:'H','A':'H'},
    '3':  {2:'P',3:'P',4:'P',5:'P',6:'P',7:'P',8:'H',9:'H',10:'H','A':'H'},
    '2':  {2:'P',3:'P',4:'P',5:'P',6:'P',7:'P',8:'H',9:'H',10:'H','A':'H'},
}

ACTION_INFO = {
    'H': {'text': 'HIT',          'color': '#22c55e', 'bg': '#052e16', 'desc': 'Húzz még egy lapot!'},
    'S': {'text': 'STAND',        'color': '#3b82f6', 'bg': '#172554', 'desc': 'Megállsz — elég erős a kezed.'},
    'D': {'text': 'DOUBLE DOWN',  'color': '#f59e0b', 'bg': '#411d02', 'desc': 'Duplázd a tétet, egy lap jár.'},
    'P': {'text': 'SPLIT',        'color': '#a855f7', 'bg': '#2e1065', 'desc': 'Osztd ketté a párod.'},
    'R': {'text': 'SURRENDER',    'color': '#ef4444', 'bg': '#3b0506', 'desc': 'Add fel — ha nem lehet: Hit.'},
}

HILO = {r: (1 if r in ['2','3','4','5','6'] else (-1 if r in ['10','J','Q','K','A'] else 0))
        for r in ['A','2','3','4','5','6','7','8','9','10','J','Q','K']}


# ── Strategy engine ────────────────────────────────────────────────────────────

def card_value(r: str) -> int:
    if r == 'A': return 11
    if r in ['J','Q','K','10']: return 10
    return int(r)

def calc_hand(cards: List[str]) -> int:
    aces = cards.count('A')
    total = sum(card_value(c) for c in cards)
    while total > 21 and aces:
        total -= 10
        aces -= 1
    return total

def is_soft(cards: List[str]) -> bool:
    """True if hand contains an Ace counted as 11 (soft hand)."""
    if 'A' not in cards: return False
    others = [c for c in cards if c != 'A']
    other_sum = sum(card_value(c) for c in others)
    return other_sum + 11 <= 21

def is_pair(cards: List[str]) -> bool:
    if len(cards) != 2: return False
    norm = lambda r: '10' if r in ['J','Q','K','10'] else r
    return norm(cards[0]) == norm(cards[1])

def get_advice(player: List[str], dealer: Optional[str]) -> Optional[dict]:
    if not player or len(player) < 2 or not dealer:
        return None
    dk_raw = '10' if dealer in ['J','Q','K'] else dealer
    try:
        dk = int(dk_raw)   # numeric dealer: 2-10
    except (ValueError, TypeError):
        dk = dk_raw        # 'A'
    hv = calc_hand(player)

    if hv > 21:
        return {'action': 'BUST', 'text': 'BUST', 'color': '#ef4444',
                'bg': '#1a0000', 'desc': 'Túl sok lap — kimentél!'}
    if hv == 21 and len(player) == 2:
        return {'action': 'BJ', 'text': 'BLACKJACK!', 'color': '#f59e0b',
                'bg': '#1c1000', 'desc': 'Természetes blackjack!'}

    if is_pair(player):
        pr = '10' if player[0] in ['J','Q','K','10'] else player[0]
        a = PAIRS.get(pr, {}).get(dk, 'H')
    elif is_soft(player):
        sv = hv
        a = SOFT.get(sv, HARD.get(min(sv,21), {})).get(dk, 'H')
    else:
        hk = min(max(hv, 5), 21)
        a = HARD.get(hk, {}).get(dk, 'S')

    info = ACTION_INFO[a]
    return {'action': a, **info}


# ── Screen reader (optional, needs tesseract) ──────────────────────────────────

def try_import_ocr():
    """Returns (mss, pytesseract, cv2, np) or None if not available."""
    try:
        import mss
        import pytesseract
        import cv2
        import numpy as np
        # Quick test
        pytesseract.get_tesseract_version()
        return mss, pytesseract, cv2, np
    except Exception:
        return None

def scan_screen_for_cards(ocr_modules) -> Tuple[List[str], Optional[str]]:
    """
    Minimal screen scan: capture full screen, OCR for card ranks.
    Returns (player_cards, dealer_card) as rank strings.
    This is a heuristic — works best on online casinos with clear card text.
    """
    mss, pytesseract, cv2, np = ocr_modules
    try:
        with mss.mss() as sct:
            monitor = sct.monitors[1]
            screenshot = sct.grab(monitor)
            img = np.array(screenshot)

        gray = cv2.cvtColor(img, cv2.COLOR_BGRA2GRAY)
        _, thresh = cv2.threshold(gray, 180, 255, cv2.THRESH_BINARY)

        config = '--psm 6 -c tessedit_char_whitelist=A23456789TJQK0'
        text = pytesseract.image_to_string(thresh, config=config)

        found = []
        for token in text.upper().split():
            token = token.strip('.,;:')
            if token in ['A','2','3','4','5','6','7','8','9']:
                found.append(token)
            elif token in ['10','T','J','Q','K']:
                found.append('10' if token == 'T' else token)

        if len(found) >= 3:
            return found[1:], found[0]
        return [], None
    except Exception:
        return [], None


# ── Main overlay window ────────────────────────────────────────────────────────

class BlackjackOverlay:
    RANKS = ['A','2','3','4','5','6','7','8','9','10','J','Q','K']
    BG       = '#0d0d0d'
    SURFACE  = '#1a1a1a'
    SURFACE2 = '#222222'
    BORDER   = '#333333'
    TEXT     = '#f0ede8'
    MUTED    = '#777770'

    def __init__(self):
        self.player_cards: List[str] = []
        self.dealer_card: Optional[str] = None
        self.running_count: int = 0
        self.hand_count: int = 0
        self.auto_mode: bool = False
        self.ocr_available = try_import_ocr()
        self.scan_thread = None
        self.running = True

        self._build_ui()

    def _build_ui(self):
        self.root = tk.Tk()
        self.root.title("Blackjack Advisor")
        self.root.geometry("420x620+50+50")
        self.root.configure(bg=self.BG)
        self.root.resizable(True, True)

        # Always on top
        self.root.attributes('-topmost', True)
        self.root.attributes('-alpha', 0.95)

        # Allow dragging
        self.root.bind('<Button-1>', self._start_drag)
        self.root.bind('<B1-Motion>', self._do_drag)
        self.root.bind('<Escape>', lambda e: self._quit())
        self.root.bind('q', lambda e: self._quit())
        self.root.bind('n', lambda e: self._clear_hand())
        self.root.bind('r', lambda e: self._full_reset())
        self.root.protocol("WM_DELETE_WINDOW", self._quit)

        self._drag_x = 0
        self._drag_y = 0

        # ── Title bar ──────────────────────────────────────────────────────────
        title_frame = tk.Frame(self.root, bg=self.BG)
        title_frame.pack(fill='x', padx=12, pady=(12,6))

        tk.Label(title_frame, text="BLACKJACK", bg=self.BG, fg=self.TEXT,
                 font=('Courier', 16, 'bold')).pack(side='left')
        tk.Label(title_frame, text="ADVISOR", bg=self.BG, fg='#22c55e',
                 font=('Courier', 16, 'bold')).pack(side='left', padx=(4,0))

        self.count_lbl = tk.Label(title_frame, text="RC: 0", bg=self.BG, fg=self.MUTED,
                                   font=('Courier', 11))
        self.count_lbl.pack(side='right')

        self._divider()

        # ── Advice display ─────────────────────────────────────────────────────
        self.advice_frame = tk.Frame(self.root, bg=self.SURFACE, bd=0,
                                      highlightbackground=self.BORDER,
                                      highlightthickness=1)
        self.advice_frame.pack(fill='x', padx=12, pady=6)

        self.advice_action = tk.Label(self.advice_frame, text="—",
                                       bg=self.SURFACE, fg=self.MUTED,
                                       font=('Courier', 32, 'bold'))
        self.advice_action.pack(pady=(12,4))

        self.advice_desc = tk.Label(self.advice_frame, text="Add meg a lapokat alul",
                                     bg=self.SURFACE, fg=self.MUTED,
                                     font=('Helvetica', 11), wraplength=340)
        self.advice_desc.pack(pady=(0,12))

        self._divider()

        # ── Player cards ───────────────────────────────────────────────────────
        player_header = tk.Frame(self.root, bg=self.BG)
        player_header.pack(fill='x', padx=12, pady=(6,2))
        tk.Label(player_header, text="TE LAPJAID", bg=self.BG, fg=self.MUTED,
                 font=('Courier', 9)).pack(side='left')
        self.hand_val_lbl = tk.Label(player_header, text="", bg=self.BG, fg=self.TEXT,
                                      font=('Courier', 9))
        self.hand_val_lbl.pack(side='right')

        self.player_frame = tk.Frame(self.root, bg=self.SURFACE,
                                      highlightbackground=self.BORDER, highlightthickness=1)
        self.player_frame.pack(fill='x', padx=12, pady=(0,8))
        self._rebuild_player_row()

        # ── Dealer card ────────────────────────────────────────────────────────
        tk.Label(self.root, text="DEALER FELSŐ LAPJA", bg=self.BG, fg=self.MUTED,
                 font=('Courier', 9)).pack(anchor='w', padx=12)

        self.dealer_frame = tk.Frame(self.root, bg=self.SURFACE,
                                      highlightbackground=self.BORDER, highlightthickness=1)
        self.dealer_frame.pack(fill='x', padx=12, pady=(2,8))
        self._rebuild_dealer_row()

        self._divider()

        # ── Quick card picker ──────────────────────────────────────────────────
        tk.Label(self.root, text="GYORS LAPVÁLASZTÓ", bg=self.BG, fg=self.MUTED,
                 font=('Courier', 9)).pack(anchor='w', padx=12, pady=(6,4))

        picker_frame = tk.Frame(self.root, bg=self.BG)
        picker_frame.pack(fill='x', padx=12)

        # Mode toggle row
        mode_row = tk.Frame(picker_frame, bg=self.BG)
        mode_row.pack(fill='x', pady=(0,4))

        tk.Label(mode_row, text="Cél:", bg=self.BG, fg=self.MUTED,
                 font=('Courier', 9)).pack(side='left')

        self.target_var = tk.StringVar(value='player')
        tk.Radiobutton(mode_row, text="Saját lap", variable=self.target_var,
                       value='player', bg=self.BG, fg=self.TEXT,
                       selectcolor=self.SURFACE2, activebackground=self.BG,
                       font=('Courier', 9)).pack(side='left', padx=(6,0))
        tk.Radiobutton(mode_row, text="Dealer", variable=self.target_var,
                       value='dealer', bg=self.BG, fg=self.TEXT,
                       selectcolor=self.SURFACE2, activebackground=self.BG,
                       font=('Courier', 9)).pack(side='left', padx=(6,0))

        # Card buttons
        btn_frame = tk.Frame(picker_frame, bg=self.BG)
        btn_frame.pack(fill='x')
        for i, rank in enumerate(self.RANKS):
            b = tk.Button(btn_frame, text=rank, width=3, height=1,
                          bg=self.SURFACE2, fg=self.TEXT, bd=0,
                          activebackground='#333', activeforeground=self.TEXT,
                          font=('Courier', 10, 'bold'), relief='flat',
                          cursor='hand2',
                          command=lambda r=rank: self._pick_card(r))
            b.grid(row=i//7, column=i%7, padx=2, pady=2, sticky='nsew')
            btn_frame.grid_columnconfigure(i%7, weight=1)

        self._divider()

        # ── Bottom buttons ─────────────────────────────────────────────────────
        btn_row = tk.Frame(self.root, bg=self.BG)
        btn_row.pack(fill='x', padx=12, pady=(6,4))

        tk.Button(btn_row, text="Új kéz (N)", bg=self.SURFACE2, fg='#22c55e',
                  bd=0, relief='flat', padx=10, pady=6, cursor='hand2',
                  font=('Courier', 10), command=self._clear_hand).pack(side='left', padx=(0,4))

        tk.Button(btn_row, text="Reset (R)", bg=self.SURFACE2, fg='#ef4444',
                  bd=0, relief='flat', padx=10, pady=6, cursor='hand2',
                  font=('Courier', 10), command=self._full_reset).pack(side='left', padx=(0,4))

        if self.ocr_available:
            self.auto_btn = tk.Button(btn_row, text="Auto OFF", bg=self.SURFACE2,
                                      fg=self.MUTED, bd=0, relief='flat',
                                      padx=10, pady=6, cursor='hand2',
                                      font=('Courier', 10), command=self._toggle_auto)
            self.auto_btn.pack(side='right')
        else:
            tk.Label(btn_row, text="OCR: nincs", bg=self.BG, fg='#ef4444',
                     font=('Courier', 9)).pack(side='right')

        # ── Status bar ─────────────────────────────────────────────────────────
        self.status_lbl = tk.Label(self.root,
                                    text="Kész  |  Q vagy Esc = kilépés  |  N = új kéz",
                                    bg=self.BG, fg=self.MUTED, font=('Courier', 9))
        self.status_lbl.pack(pady=(2,8))

        self._update_advice()

    # ── UI helpers ─────────────────────────────────────────────────────────────

    def _divider(self):
        tk.Frame(self.root, bg=self.BORDER, height=1).pack(fill='x', padx=12, pady=4)

    def _start_drag(self, e):
        self._drag_x = e.x_root - self.root.winfo_x()
        self._drag_y = e.y_root - self.root.winfo_y()

    def _do_drag(self, e):
        x = e.x_root - self._drag_x
        y = e.y_root - self._drag_y
        self.root.geometry(f"+{x}+{y}")

    def _card_chip(self, parent, rank: str, on_remove):
        """Render a mini card chip."""
        f = tk.Frame(parent, bg='#fafaf8', bd=0, padx=4, pady=2)
        is_red = rank in ['A','K','Q','J']  # simplified — no suit tracking here
        color = '#c0392b' if is_red else '#1a1a1a'
        tk.Label(f, text=rank, bg='#fafaf8', fg=color,
                 font=('Courier', 13, 'bold')).pack()
        tk.Button(f, text='×', bg='#fafaf8', fg='#999', bd=0, relief='flat',
                  font=('Courier', 8), cursor='hand2',
                  command=on_remove).pack()
        return f

    def _rebuild_player_row(self):
        for w in self.player_frame.winfo_children():
            w.destroy()

        row = tk.Frame(self.player_frame, bg=self.SURFACE)
        row.pack(fill='x', padx=6, pady=6)

        for i, r in enumerate(self.player_cards):
            chip = self._card_chip(row, r, lambda idx=i: self._remove_player(idx))
            chip.pack(side='left', padx=2)

        if len(self.player_cards) < 8:
            tk.Button(row, text="+", bg=self.SURFACE2, fg=self.MUTED,
                      bd=0, relief='flat', width=3, height=2, cursor='hand2',
                      font=('Courier', 14),
                      command=lambda: self._set_target_and_focus('player')).pack(side='left', padx=2)

    def _rebuild_dealer_row(self):
        for w in self.dealer_frame.winfo_children():
            w.destroy()

        row = tk.Frame(self.dealer_frame, bg=self.SURFACE)
        row.pack(fill='x', padx=6, pady=6)

        if self.dealer_card:
            chip = self._card_chip(row, self.dealer_card, self._remove_dealer)
            chip.pack(side='left', padx=2)
        else:
            tk.Button(row, text="+", bg=self.SURFACE2, fg=self.MUTED,
                      bd=0, relief='flat', width=3, height=2, cursor='hand2',
                      font=('Courier', 14),
                      command=lambda: self._set_target_and_focus('dealer')).pack(side='left', padx=2)

    def _set_target_and_focus(self, target: str):
        self.target_var.set(target)

    def _pick_card(self, rank: str):
        target = self.target_var.get()
        if target == 'player':
            self.player_cards.append(rank)
            self.running_count += HILO[rank]
        else:
            if self.dealer_card:
                self.running_count -= HILO[self.dealer_card]
            self.dealer_card = rank
            self.running_count += HILO[rank]
            self.target_var.set('player')  # auto-switch back
        self._refresh()

    def _remove_player(self, idx: int):
        r = self.player_cards.pop(idx)
        self.running_count -= HILO[r]
        self._refresh()

    def _remove_dealer(self):
        if self.dealer_card:
            self.running_count -= HILO[self.dealer_card]
            self.dealer_card = None
        self._refresh()

    def _clear_hand(self):
        self.player_cards = []
        self.dealer_card = None
        self._refresh()

    def _full_reset(self):
        self.player_cards = []
        self.dealer_card = None
        self.running_count = 0
        self.hand_count = 0
        self._refresh()
        self._set_status("Mindent töröltünk")

    def _update_advice(self):
        adv = get_advice(self.player_cards, self.dealer_card)

        if not adv:
            self.advice_action.config(text="—", fg=self.MUTED, bg=self.SURFACE)
            self.advice_desc.config(text="Add meg a lapokat (min 2 saját + 1 dealer)",
                                    fg=self.MUTED, bg=self.SURFACE)
            self.advice_frame.config(highlightbackground=self.BORDER)
        else:
            self.advice_action.config(text=adv['text'], fg=adv['color'], bg=adv['bg'])
            self.advice_desc.config(text=adv['desc'], fg=adv.get('color','#fff'), bg=adv['bg'])
            self.advice_frame.config(bg=adv['bg'], highlightbackground=adv['color'])
            self.advice_action.config(bg=adv['bg'])

        # Hand value
        if self.player_cards:
            hv = calc_hand(self.player_cards)
            type_str = ''
            if len(self.player_cards)==2 and is_pair(self.player_cards): type_str='Pár'
            elif is_soft(self.player_cards): type_str='Puha'
            else: type_str='Kemény'
            color = '#ef4444' if hv>21 else ('#f59e0b' if hv==21 and len(self.player_cards)==2 else self.TEXT)
            self.hand_val_lbl.config(text=f"BUST" if hv>21 else f"{type_str} {hv}", fg=color)
        else:
            self.hand_val_lbl.config(text="", fg=self.TEXT)

        # Running count
        rc = self.running_count
        rc_color = '#22c55e' if rc>0 else ('#ef4444' if rc<0 else self.MUTED)
        self.count_lbl.config(text=f"RC: {'+' if rc>0 else ''}{rc}", fg=rc_color)

    def _refresh(self):
        self._rebuild_player_row()
        self._rebuild_dealer_row()
        self._update_advice()

    def _set_status(self, msg: str):
        self.status_lbl.config(text=msg)
        self.root.after(3000, lambda: self.status_lbl.config(
            text="Kész  |  Q vagy Esc = kilépés  |  N = új kéz"))

    # ── Auto OCR mode ──────────────────────────────────────────────────────────

    def _toggle_auto(self):
        self.auto_mode = not self.auto_mode
        if self.auto_mode:
            self.auto_btn.config(text="Auto ON", fg='#22c55e')
            self._set_status("Auto mód aktív — képernyőfigyelés...")
            self._start_scan_thread()
        else:
            self.auto_btn.config(text="Auto OFF", fg=self.MUTED)
            self._set_status("Auto mód kikapcsolva")

    def _start_scan_thread(self):
        def scan_loop():
            while self.auto_mode and self.running:
                player, dealer = scan_screen_for_cards(self.ocr_available)
                if player or dealer:
                    self.root.after(0, lambda p=player, d=dealer: self._apply_scan(p, d))
                time.sleep(2)

        self.scan_thread = threading.Thread(target=scan_loop, daemon=True)
        self.scan_thread.start()

    def _apply_scan(self, player: List[str], dealer: Optional[str]):
        changed = False
        if player and set(player) != set(self.player_cards):
            self.player_cards = player
            changed = True
        if dealer and dealer != self.dealer_card:
            self.dealer_card = dealer
            changed = True
        if changed:
            self._refresh()
            self._set_status(f"Frissítve: {player} | dealer: {dealer}")

    # ── Quit ───────────────────────────────────────────────────────────────────

    def _quit(self):
        self.running = False
        self.auto_mode = False
        self.root.destroy()

    def run(self):
        self.root.mainloop()


# ── Entry point ────────────────────────────────────────────────────────────────

if __name__ == '__main__':
    print("=" * 50)
    print("  BLACKJACK STRATEGY OVERLAY")
    print("=" * 50)
    print()
    print("  Billentyűk:")
    print("    P        → saját lap mód")
    print("    D        → dealer lap mód")
    print("    N        → új kéz")
    print("    R        → teljes reset")
    print("    Esc / Q  → kilépés")
    print()

    ocr = try_import_ocr()
    if ocr:
        print("  [OK] OCR (Tesseract) elérhető — Auto mód aktív")
    else:
        print("  [--] OCR nem elérhető — csak manuális mód")
        print("       Telepítés: pip install pytesseract mss opencv-python")
        print("       + Tesseract: brew install tesseract / apt install tesseract-ocr")
    print()
    print("  Overlay indul...")
    print()

    app = BlackjackOverlay()
    app.run()
