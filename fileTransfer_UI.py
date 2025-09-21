import os
import shutil
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from datetime import datetime
from PIL import Image
import json
import logging

# --- Logging Setup ---
logging.basicConfig(filename='photo_transfer.log', level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s')

# --- Tkinter setup ---
root = tk.Tk()
root.title("Phone Media Manager")

root.attributes('-fullscreen', False)

# Styling
style = ttk.Style()
try:
    style.theme_use('clam')
except Exception:
    pass

PRIMARY_BG = '#0f1115'
SECONDARY_BG = '#151924'
ACCENT = '#7aa2f7'
ACCENT_HOVER = '#8fb5ff'
TEXT_PRIMARY = '#e5e9f0'
TEXT_SECONDARY = '#a9b1d6'

root.configure(bg=PRIMARY_BG)

style.configure('TFrame', background=PRIMARY_BG)
style.configure('Secondary.TFrame', background=SECONDARY_BG)
style.configure('Header.TLabel', background=PRIMARY_BG, foreground=TEXT_PRIMARY,
                font=('Segoe UI', 24, 'bold'))
style.configure('Subheader.TLabel', background=PRIMARY_BG, foreground=TEXT_SECONDARY,
                font=('Segoe UI', 12))
style.configure('Card.TFrame', background=SECONDARY_BG)
style.configure('Primary.TButton', font=('Segoe UI', 12, 'bold'), padding=(16, 12))
style.map('Primary.TButton',
          background=[('!disabled', SECONDARY_BG), ('active', '#1b2130')],
          foreground=[('!disabled', TEXT_PRIMARY)],
          relief=[('pressed', 'sunken'), ('!pressed', 'raised')])
style.configure('Primary.TButton', background=SECONDARY_BG, foreground=TEXT_PRIMARY, borderwidth=0)
style.configure('Accent.TButton', font=('Segoe UI', 12, 'bold'), padding=(16, 12),
                background=ACCENT, foreground='#0b0e14')
style.map('Accent.TButton', background=[('active', ACCENT_HOVER)])
style.configure('Body.TLabel', background=PRIMARY_BG, foreground=TEXT_SECONDARY, font=('Segoe UI', 10))
# Ensure base layout exists for custom progressbar style
style.layout('lux.Progressbar', style.layout('Horizontal.TProgressbar'))
style.configure('lux.Progressbar', troughcolor=SECONDARY_BG, background=ACCENT, bordercolor=SECONDARY_BG,
                lightcolor=ACCENT, darkcolor=ACCENT)

# --- File extensions ---
image_extensions = ('.jpg', '.jpeg', '.png', '.heic')
video_extensions = ('.mp4', '.mov', '.avi', '.mkv')

# --- Helper to get file date ---
def get_file_date(file_path):
    try:
        if file_path.lower().endswith(image_extensions):
            img = Image.open(file_path)
            exif_data = img._getexif()
            if exif_data:
                date_str = exif_data.get(36867)
                if date_str:
                    return datetime.strptime(date_str, '%Y:%m:%d %H:%M:%S')
        timestamp = os.path.getmtime(file_path)
        return datetime.fromtimestamp(timestamp)
    except Exception as e:
        logging.warning(f"Cannot read metadata for {file_path}: {e}")
        return datetime.fromtimestamp(os.path.getmtime(file_path))

# --- Locked JSON log file path ---
log_file = 'transfer_log.json'

def load_transfer_log():
    if os.path.exists(log_file):
        try:
            with open(log_file, 'r') as f:
                return json.load(f)
        except Exception:
            return {}
    return {}

def save_transfer_log(data):
    with open(log_file, 'w') as f:
        json.dump(data, f, indent=4)

# --- Initialize transfer log (create if missing, then read) ---
def ensure_transfer_log_file():
    if not os.path.exists(log_file):
        try:
            with open(log_file, 'w') as f:
                json.dump({}, f)
        except Exception:
            pass

ensure_transfer_log_file()
# Global in-memory store for the transfer log
transfer_log = load_transfer_log()

# --- Center Window Helper ---
def center_window(win, width=None, height=None):
    win.update_idletasks()
    if width is None or height is None:
        width = win.winfo_width()
        height = win.winfo_height()
    x = (win.winfo_screenwidth() // 2) - (width // 2)
    y = (win.winfo_screenheight() // 2) - (height // 2)
    win.geometry(f"{width}x{height}+{x}+{y}")

# --- Transfer Function ---
def transfer_files():
    source_folder = filedialog.askdirectory(title="Select Source Folder")
    if not source_folder:
        return

    # Date range dialog
    def date_range_dialog(parent):
        months = [
            (1, 'January'), (2, 'February'), (3, 'March'), (4, 'April'),
            (5, 'May'), (6, 'June'), (7, 'July'), (8, 'August'),
            (9, 'September'), (10, 'October'), (11, 'November'), (12, 'December')
        ]
        years = list(range(2000, datetime.now().year + 1))
        days = list(range(1, 32))

        dlg = tk.Toplevel(parent)
        dlg.title("Select Date Range")
        dlg.configure(bg=PRIMARY_BG)
        dlg.transient(parent)
        dlg.grab_set()

        frame = ttk.Frame(dlg, style='Secondary.TFrame')
        frame.pack(padx=24, pady=24, fill='both', expand=True)

        # Start Date
        ttk.Label(frame, text="Start Date", style='Header.TLabel').grid(row=0, column=0, columnspan=6, sticky='w', pady=(0, 6))
        start_day = ttk.Combobox(frame, values=days, state='readonly', width=5)
        start_day.current(0)
        start_day.grid(row=1, column=0, padx=(0,8), pady=(0,12))
        start_month = ttk.Combobox(frame, values=[m[1] for m in months], state='readonly', width=12)
        start_month.current(0)
        start_month.grid(row=1, column=2, padx=(0,8), pady=(0,12))
        start_year = ttk.Combobox(frame, values=years, state='readonly', width=8)
        start_year.current(0)
        start_year.grid(row=1, column=4, padx=(0,8), pady=(0,12))

        # End Date
        ttk.Label(frame, text="End Date", style='Header.TLabel').grid(row=2, column=0, columnspan=6, sticky='w', pady=(6,6))
        end_day = ttk.Combobox(frame, values=days, state='readonly', width=5)
        end_day.current(datetime.now().day-1)
        end_day.grid(row=3, column=0, padx=(0,8), pady=(0,12))
        end_month = ttk.Combobox(frame, values=[m[1] for m in months], state='readonly', width=12)
        end_month.current(datetime.now().month-1)
        end_month.grid(row=3, column=2, padx=(0,8), pady=(0,12))
        end_year = ttk.Combobox(frame, values=years, state='readonly', width=8)
        end_year.current(len(years)-1)
        end_year.grid(row=3, column=4, padx=(0,8), pady=(0,12))

        result = {'ok': False}

        def on_ok():
            try:
                sd = int(start_day.get())
                sm = [m[0] for m in months if m[1]==start_month.get()][0]
                sy = int(start_year.get())
                ed = int(end_day.get())
                em = [m[0] for m in months if m[1]==end_month.get()][0]
                ey = int(end_year.get())
                start_dt = datetime(sy, sm, sd)
                end_dt = datetime(ey, em, ed, 23,59,59)
                if start_dt > end_dt:
                    messagebox.showerror("Error", "Start date must be before end date.", parent=dlg)
                    return
                result['ok'] = True
                result['start'] = start_dt
                result['end'] = end_dt
                dlg.destroy()
            except Exception:
                messagebox.showerror("Error", "Invalid date selection.", parent=dlg)

        def on_cancel():
            dlg.destroy()

        btns = ttk.Frame(frame, style='Secondary.TFrame')
        btns.grid(row=4, column=0, columnspan=6, sticky='e')
        ttk.Button(btns, text="OK", style='Accent.TButton', command=on_ok).grid(row=0,column=0,padx=8)
        ttk.Button(btns, text="Cancel", style='Primary.TButton', command=on_cancel).grid(row=0,column=1)

        dlg.update_idletasks()
        center_window(dlg, 520, 280)
        dlg.wait_window()
        if result.get('ok'):
            return result['start'], result['end']
        return None

    date_range = date_range_dialog(root)
    if not date_range:
        return
    start_dt, end_dt = date_range

    # Collect media files
    matched_files = []
    for root_dir, _, files in os.walk(source_folder):
        for file in files:
            if file.lower().endswith(image_extensions + video_extensions):
                full_path = os.path.join(root_dir, file)
                dt = get_file_date(full_path)
                if start_dt <= dt <= end_dt:
                    matched_files.append((full_path, dt))

    if not matched_files:
        messagebox.showinfo("No files", "No media files found in the selected date range.")
        return

    dest_folder = filedialog.askdirectory(title="Select Destination Folder")
    if not dest_folder:
        return

    # Progress window
    progress_window = tk.Toplevel(root)
    progress_window.title("Transferring Files")
    progress_window.configure(bg=PRIMARY_BG)
    progress_window.transient(root)
    progress_window.grab_set()

    container = ttk.Frame(progress_window, style='Secondary.TFrame')
    container.pack(padx=24, pady=24, fill='both', expand=True)
    progress_label = ttk.Label(container, text="Starting...", style='Body.TLabel')
    progress_label.pack(padx=10, pady=(10,6), anchor='w')
    progress_bar = ttk.Progressbar(container, length=500, mode='determinate', style='lux.Progressbar')
    progress_bar.pack(padx=10, pady=(0,10), fill='x')
    progress_bar['maximum'] = len(matched_files)
    progress_window.update_idletasks()
    center_window(progress_window, 640, 160)

    transfer_log = load_transfer_log()
    transferred_files = []

    # Establish a session identifier for this transfer operation
    session_id = datetime.now().isoformat()
    session_started_at = session_id

    for idx, (src_file, file_date) in enumerate(matched_files, 1):
        progress_label.config(text=f"Processing {os.path.basename(src_file)} ({idx}/{len(matched_files)})")
        progress_window.update()

        month_folder = os.path.join(dest_folder, f"{file_date.year}-{file_date.month:02}")
        os.makedirs(month_folder, exist_ok=True)
        dest_file = os.path.join(month_folder, os.path.basename(src_file))

        try:
            shutil.copy2(src_file, dest_file)
            logging.info(f"Copied {src_file} -> {dest_file}")
            transferred_files.append(src_file)

            # Update structured JSON transfer log per file
            if not isinstance(transfer_log, dict):
                # Safety: re-load or reset if corrupted
                current = load_transfer_log()
                transfer_log.clear() if isinstance(transfer_log, dict) else None
                if isinstance(current, dict):
                    transfer_log.update(current)
                else:
                    transfer_log.clear()
            entries = transfer_log.setdefault('entries', [])
            entry = {
                'source': src_file,
                'destination': dest_file,
                'timestamp': datetime.now().isoformat(),
                'session_id': session_id,
                'session_started_at': session_started_at,
                'session_source': source_folder,
                'session_destination': dest_folder
            }
            # Update if destination already exists, else append
            updated = False
            for i, e in enumerate(entries):
                if isinstance(e, dict) and e.get('destination') == dest_file:
                    entries[i] = entry
                    updated = True
                    break
            if not updated:
                entries.append(entry)
            save_transfer_log(transfer_log)
            # refresh session logs pane if visible
            refresh_session_logs()
        except Exception as e:
            logging.error(f"Error copying {src_file} -> {dest_file}: {e}")

        progress_bar['value'] = idx
        progress_window.update()

    progress_window.destroy()

    if 'transfers' not in transfer_log:
        transfer_log['transfers'] = []
    transfer_log['transfers'].extend(transferred_files)
    save_transfer_log(transfer_log)

    messagebox.showinfo("Done", f"Transfer completed! {len(transferred_files)} files transferred.")

    # Session summary log for UI consumption
    try:
        logging.info(f"SESSION_SUMMARY files={len(transferred_files)} source={source_folder} dest={dest_folder}")
    except Exception:
        pass

# --- Delete Function ---
def delete_transferred_files():
    # New flow: delete files at source by selecting a session and entries
    data = load_transfer_log()
    entries = data.get('entries', []) if isinstance(data, dict) else []
    if not entries:
        messagebox.showinfo("No files", "No transfer entries found.")
        return

    # Build sessions list from entries
    sessions = {}
    for e in entries:
        sid = e.get('session_id') or 'unknown'
        sessions.setdefault(sid, {'started': e.get('session_started_at') or e.get('timestamp'),
                                  'source': e.get('session_source'),
                                  'dest': e.get('session_destination'),
                                  'items': []})
        sessions[sid]['items'].append(e)

    # Modal to select a session
    dlg = tk.Toplevel(root)
    dlg.title('Delete Files at Source')
    dlg.configure(bg=PRIMARY_BG)
    dlg.transient(root)
    dlg.grab_set()

    frame = ttk.Frame(dlg, style='Secondary.TFrame')
    frame.pack(fill='both', expand=True, padx=16, pady=16)

    ttk.Label(frame, text='Select a session:', style='Body.TLabel').pack(anchor='w', pady=(0,6))
    session_ids = list(sessions.keys())
    session_combo = ttk.Combobox(frame, values=session_ids, state='readonly')
    if session_ids:
        session_combo.current(0)
    session_combo.pack(fill='x')

    list_frame = ttk.Frame(frame, style='Secondary.TFrame')
    list_frame.pack(fill='both', expand=True, pady=(12, 8))

    # Add select all checkbox
    select_all_var = tk.BooleanVar()
    select_all_cb = ttk.Checkbutton(list_frame, text="Select All Files", variable=select_all_var, style='Body.TLabel')
    select_all_cb.pack(anchor='w', pady=(0, 4))

    cols = ('selection', 'source', 'destination', 'timestamp')
    tree = ttk.Treeview(list_frame, columns=cols, show='headings', selectmode='none')
    for c, text in zip(cols, ['Selection', 'Source', 'Destination', 'Timestamp']):
        tree.heading(c, text=text)
    tree.column('selection', width=100, anchor='center')
    tree.column('source', width=400, anchor='w')
    tree.column('destination', width=400, anchor='w')
    tree.column('timestamp', width=200, anchor='w')
    tree.pack(fill='both', expand=True)

    # Add checkbox column
    checkboxes = {}
    checkbox_frame = ttk.Frame(list_frame, style='Secondary.TFrame')
    checkbox_frame.pack(fill='x', pady=(4, 0))

    def refresh_items(*_):
        for i in tree.get_children():
            tree.delete(i)
        # Clear old checkboxes
        for widget in checkbox_frame.winfo_children():
            widget.destroy()
        checkboxes.clear()

        sid = session_combo.get()
        row_idx = 0
        for e in sessions.get(sid, {}).get('items', []):
            item = tree.insert('', 'end', values=('', e.get('source'), e.get('destination'), e.get('timestamp')))
            # Add checkbox for this row
            var = tk.BooleanVar()
            cb = ttk.Checkbutton(checkbox_frame, variable=var)
            cb.grid(row=row_idx, column=0, padx=(20, 8), pady=2)  # Increased left padding to align with Selection column
            checkboxes[item] = var
            row_idx += 1
        # Reset select all checkbox when session changes
        select_all_var.set(False)

    session_combo.bind('<<ComboboxSelected>>', refresh_items)
    refresh_items()

    def on_select_all():
        state = select_all_var.get()
        for var in checkboxes.values():
            var.set(state)

    select_all_cb.configure(command=on_select_all)

    btns = ttk.Frame(frame, style='Secondary.TFrame')
    btns.pack(fill='x')
    status_var_local = tk.StringVar(value='')
    status_label = ttk.Label(frame, textvariable=status_var_local, style='Body.TLabel')
    status_label.pack(anchor='w', pady=(6, 0))

    def on_delete():
        # Get selected from checkboxes instead of tree selection
        selected_items = [item for item, var in checkboxes.items() if var.get()]
        if not selected_items:
            status_var_local.set('Select one or more items to delete.')
            return
        to_delete_sources = []
        values_list = [tree.item(i, 'values') for i in selected_items]
        for v in values_list:
            src = v[1]  # Source is now at index 1
            to_delete_sources.append(src)

        deleted = 0
        missing = 0
        new_entries = []
        for e in entries:
            if e.get('source') in to_delete_sources:
                src_path = e.get('source')
                if src_path and os.path.exists(src_path):
                    try:
                        os.remove(src_path)
                        deleted += 1
                    except Exception as ex:
                        logging.error(f"Failed to delete source {src_path}: {ex}")
                        # keep entry if deletion failed
                        new_entries.append(e)
                        continue
                else:
                    # already gone
                    missing += 1
                # removed from log regardless if missing or deleted
            else:
                new_entries.append(e)

        data['entries'] = new_entries
        save_transfer_log(data)

        if missing and not deleted:
            messagebox.showinfo('Info', 'data previously deleted')
        else:
            messagebox.showinfo('Done', f'Deleted {deleted} file(s).{" Some data previously deleted." if missing else ""}')
        dlg.destroy()

    ttk.Button(btns, text='Delete Selected at Source', style='Accent.TButton', command=on_delete).pack(side='right')
    ttk.Button(btns, text='Cancel', style='Primary.TButton', command=dlg.destroy).pack(side='right', padx=(0,8))

    dlg.update_idletasks()
    center_window(dlg, 1200, 600)  # Increased dialog width to accommodate larger table

# --- Logs Viewer ---
def parse_session_summaries():
    sessions = []
    log_path = 'photo_transfer.log'
    if not os.path.exists(log_path):
        return sessions
    try:
        with open(log_path, 'r', encoding='utf-8', errors='ignore') as f:
            for line in f:
                # Expect format: "YYYY-MM-DD HH:MM:SS,ms - LEVEL - SESSION_SUMMARY files=.. source=.. dest=.."
                if 'SESSION_SUMMARY' not in line:
                    continue
                try:
                    parts = line.split(' - ', 2)
                    timestamp_str = parts[0].strip()
                    msg = parts[2]
                    # parse fields
                    files_part = msg.split('files=', 1)[1]
                    files_count = int(files_part.split()[0])
                    source_part = msg.split('source=', 1)[1]
                    source_path = source_part.split(' dest=', 1)[0].strip()
                    dest_part = msg.split('dest=', 1)[1]
                    dest_path = dest_part.strip()
                    # parse timestamp
                    when = None
                    for fmt in ('%Y-%m-%d %H:%M:%S,%f', '%Y-%m-%d %H:%M:%S'):
                        try:
                            when = datetime.strptime(timestamp_str, fmt)
                            break
                        except Exception:
                            continue
                    sessions.append({
                        'timestamp': when or timestamp_str,
                        'files': files_count,
                        'source': source_path,
                        'dest': dest_path,
                    })
                except Exception:
                    continue
    except Exception:
        return sessions
    return sessions


def view_logs():
    rows = parse_session_summaries()
    dlg = tk.Toplevel(root)
    dlg.title('Transfer Sessions')
    dlg.configure(bg=PRIMARY_BG)
    dlg.transient(root)
    dlg.grab_set()

    frame = ttk.Frame(dlg, style='Secondary.TFrame')
    frame.pack(fill='both', expand=True, padx=16, pady=16)

    columns = ('session', 'when', 'files', 'source', 'dest')
    tree = ttk.Treeview(frame, columns=columns, show='headings')
    tree.heading('session', text='Session')
    tree.heading('when', text='When')
    tree.heading('files', text='Files')
    tree.heading('source', text='Source')
    tree.heading('dest', text='Destination')
    tree.column('session', width=80, anchor='center')
    tree.column('when', width=220, anchor='w')
    tree.column('files', width=80, anchor='e')
    tree.column('source', width=320, anchor='w')
    tree.column('dest', width=320, anchor='w')
    tree.pack(fill='both', expand=True)

    # Insert rows with friendly formatting
    for idx, r in enumerate(rows, start=1):
        ts = r['timestamp']
        if isinstance(ts, datetime):
            when_str = ts.strftime('%d %B %Y %I:%M %p')
        else:
            when_str = str(ts)
        tree.insert('', 'end', values=(idx, when_str, r['files'], r['source'], r['dest']))

    btns = ttk.Frame(frame, style='Secondary.TFrame')
    btns.pack(fill='x', pady=(8, 0))
    ttk.Button(btns, text='Close', style='Primary.TButton', command=dlg.destroy).pack(side='right')


# --- Raw Audit Log Viewer (read-only) ---
def view_audit_log():
    dlg = tk.Toplevel(root)
    dlg.title('Audit Log - photo_transfer.log')
    dlg.configure(bg=PRIMARY_BG)
    dlg.transient(root)
    dlg.grab_set()

    frame = ttk.Frame(dlg, style='Secondary.TFrame')
    frame.pack(fill='both', expand=True, padx=12, pady=12)

    # Toolbar
    top = ttk.Frame(frame, style='Secondary.TFrame')
    top.pack(fill='x', pady=(0,6))
    ttk.Label(top, text='Read-only audit log view', style='Body.TLabel').pack(side='left')
    ttk.Button(top, text='Close', style='Primary.TButton', command=dlg.destroy).pack(side='right')

    # Text area with scrollbar (read-only)
    text_frame = ttk.Frame(frame, style='Secondary.TFrame')
    text_frame.pack(fill='both', expand=True)

    scrollbar = ttk.Scrollbar(text_frame, orient='vertical')
    text = tk.Text(text_frame, wrap='none', bg=PRIMARY_BG, fg=TEXT_SECONDARY, insertbackground=TEXT_PRIMARY,
                   relief='flat')
    text.configure(state='normal')
    text.pack(side='left', fill='both', expand=True)
    scrollbar.config(command=text.yview)
    text.configure(yscrollcommand=scrollbar.set)
    scrollbar.pack(side='right', fill='y')

    # Load log content
    log_path = 'photo_transfer.log'
    content = ''
    if os.path.exists(log_path):
        try:
            with open(log_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
        except Exception as e:
            content = f"Failed to read log: {e}"
    else:
        content = 'Log file not found. It will be created as transfers occur.'

    text.insert('1.0', content)
    text.configure(state='disabled')

# --- Session logs refresher (global hook) ---
session_logs_tree = None

def refresh_session_logs():
    global session_logs_tree
    if session_logs_tree is None:
        return
    # Clear
    for i in session_logs_tree.get_children():
        session_logs_tree.delete(i)
    data = load_transfer_log()
    entries = data.get('entries', []) if isinstance(data, dict) else []
    # Group by session
    grouped = {}
    for e in entries:
        sid = e.get('session_id') or 'unknown'
        grouped.setdefault(sid, {
            'when': e.get('session_started_at') or e.get('timestamp'),
            'source': e.get('session_source'),
            'dest': e.get('session_destination'),
            'count': 0
        })
        grouped[sid]['count'] += 1
    # Insert
    idx = 1
    for sid, info in sorted(grouped.items(), key=lambda x: str(x[1]['when'])):
        ts = info['when']
        when_str = ts
        if isinstance(ts, str):
            try:
                dt = datetime.fromisoformat(ts.replace('Z', '+00:00'))
                when_str = dt.strftime('%d %B %Y %I:%M %p')
            except Exception:
                pass
        session_logs_tree.insert('', 'end', values=(idx, when_str, info['count'], info['source'], info['dest']))
        idx += 1

# --- Main View ---
def build_main_view():
    root.columnconfigure(0, weight=1)
    root.rowconfigure(0, weight=1)

    outer = ttk.Frame(root)
    outer.grid(row=0, column=0, sticky='nsew')
    outer.rowconfigure(1, weight=1)
    outer.columnconfigure(1, weight=1)

    card = ttk.Frame(outer, style='Card.TFrame')
    card.grid(row=1, column=1, sticky='nsew', padx=40, pady=40)
    card.rowconfigure(2, weight=1)
    card.columnconfigure(0, weight=1)

    header = ttk.Label(card, text="Phone Media Manager", style='Header.TLabel')
    header.grid(row=0, column=0, padx=32, pady=(32,6), sticky='w')

    subheader = ttk.Label(card, text="Organize and transfer your photos and videos by month and year.",
                          style='Subheader.TLabel')
    subheader.grid(row=1, column=0, padx=32, pady=(0,24), sticky='w')

    # Two-column content: actions (left), session logs (right)
    content = ttk.Frame(card, style='Card.TFrame')
    content.grid(row=2, column=0, padx=32, pady=(0,32), sticky='nsew')
    content.columnconfigure(0, weight=0)
    content.columnconfigure(1, weight=1)
    content.rowconfigure(0, weight=1)

    # Left actions
    buttons = ttk.Frame(content, style='Card.TFrame')
    buttons.grid(row=0, column=0, sticky='n')

    transfer_btn = ttk.Button(buttons, text="Transfer Photos / Videos", style='Accent.TButton', command=transfer_files)
    transfer_btn.grid(row=0, column=0, pady=(0,12), sticky='ew')
    del_source_btn = ttk.Button(buttons, text="Delete Files at Source", style='Primary.TButton', command=delete_transferred_files)
    del_source_btn.grid(row=1, column=0, pady=(0,12), sticky='ew')
    audit_btn = ttk.Button(buttons, text="View Audit Log (.log)", style='Primary.TButton', command=view_audit_log)
    audit_btn.grid(row=2, column=0, pady=(0,12), sticky='ew')
    exit_btn = ttk.Button(buttons, text="Exit", style='Primary.TButton', command=root.destroy)
    exit_btn.grid(row=3, column=0, sticky='ew')

    # Right session logs table
    right = ttk.Frame(content, style='Card.TFrame')
    right.grid(row=0, column=1, sticky='nsew')
    right.rowconfigure(1, weight=1)
    right.columnconfigure(0, weight=1)

    ttk.Label(right, text='Session Logs', style='Subheader.TLabel').grid(row=0, column=0, sticky='w', pady=(0,8))
    columns = ('session', 'when', 'files', 'source', 'dest')
    tree = ttk.Treeview(right, columns=columns, show='headings')
    tree.heading('session', text='Session')
    tree.heading('when', text='When')
    tree.heading('files', text='Files')
    tree.heading('source', text='Source')
    tree.heading('dest', text='Destination')
    tree.column('session', width=80, anchor='center')
    tree.column('when', width=200, anchor='w')
    tree.column('files', width=80, anchor='e')
    tree.column('source', width=260, anchor='w')
    tree.column('dest', width=260, anchor='w')
    tree.grid(row=1, column=0, sticky='nsew')

    scroll = ttk.Scrollbar(right, orient='vertical', command=tree.yview)
    tree.configure(yscrollcommand=scroll.set)
    scroll.grid(row=1, column=1, sticky='ns')

    # set global reference and populate
    global session_logs_tree
    session_logs_tree = tree
    refresh_session_logs()

build_main_view()
center_window(root, 1100, 720)
root.mainloop()
