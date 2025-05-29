import tkinter as tk
from tkinter import ttk, messagebox
import re
from datetime import datetime, timedelta
from typing import List, Tuple
import holidays

# ====== 기능 1: 커밋 메시지 생성 ======
def process_message(message: str) -> str:
    if not message:
        return "커밋메시지"
    first_char = message[0]
    if re.match(r"[A-Z]", first_char):
        message = first_char.lower() + message[1:]
    elif re.match(r"[가-힣]", first_char):
        message = f"contents - {message}"
    return message

def generate_commit_and_branch(jira_ticket_no: str, message: str = "커밋메시지"):
    processed_msg = process_message(message)
    commit_msg = f"git commit -m \"feat(HMGPROD-{jira_ticket_no}): {processed_msg}\""
    branch_name = f"feature/HMGPROD-{jira_ticket_no}"
    switch1_name = f"git switch {branch_name}"
    switch2_name = f"git switch -c {branch_name}"
    return commit_msg, branch_name, switch1_name, switch2_name  # ✅ 수정됨!

# ====== 기능 2: 케이스 변환 ======
def generate_case_variants(input_string: str) -> dict:
    words = input_string.strip().split()
    if not words:
        return {}
    camel = words[0].lower() + ''.join(word.capitalize() for word in words[1:])
    pascal = ''.join(word.capitalize() for word in words)
    upper_snake = '_'.join(word.upper() for word in words)
    kebab = '-'.join(word.lower() for word in words)
    snake = '_'.join(word.lower() for word in words)
    return {
        "camelCase": camel,
        "PascalCase": pascal,
        "UPPER_SNAKE_CASE": upper_snake,
        "kebab-case": kebab,
        "snake_case": snake,
    }
def copy_text_from_widget(widget):
    if isinstance(widget, tk.Entry):
        text = widget.get().strip()
    elif isinstance(widget, tk.Text):
        text = widget.get("1.0", tk.END).strip()
    else:
        return
    if text:
        root.clipboard_clear()
        root.clipboard_append(text)

def update_case_outputs(input_str: str):
    result = generate_case_variants(input_str.strip())
    if not result:
        messagebox.showwarning("입력 오류", "⚠️ 입력 문자열이 없습니다.")
        return

    # 기존 출력 클리어
    for widget in list(case_labels.values()):
        widget["label"].destroy()
        widget["entry"].destroy()
        widget["button"].destroy()
    case_labels.clear()

    # 새로 출력
    for i, (style, value) in enumerate(result.items(), start=1):
        lbl = tk.Label(case_tab, text=style, anchor="e", width=20)
        lbl.grid(row=i, column=0, sticky="e")

        out = tk.Entry(case_tab, width=50)
        out.grid(row=i, column=1, padx=5)
        out.insert(0, value)
        out.config(state="readonly")

        btn = tk.Button(case_tab, text="복사", command=lambda e=out: copy_text_from_widget(e))
        btn.grid(row=i, column=2)

        case_labels[style] = {"label": lbl, "entry": out, "button": btn}

# ====== 기능 3: 워킹데이 일정 계산 ======
kr_holidays = holidays.KR()

def is_workday(d: datetime) -> bool:
    return d.weekday() < 5 and d not in kr_holidays

def next_workday(d: datetime) -> datetime:
    while True:
        d += timedelta(days=1)
        if is_workday(d):
            return d

def add_workdays(start_date: datetime, num_days: int) -> datetime:
    current = start_date
    added = 0
    while True:
        if is_workday(current):
            added += 1
            if added == num_days:
                return current
        current += timedelta(days=1)

def generate_schedule_with_holidays(
    tasks: List[Tuple[str, int]],
    initial_start: str
):
    current_start = datetime.strptime(initial_start, "%Y-%m-%d")
    schedule = []

    for name, duration in tasks:
        end = add_workdays(current_start, duration)
        schedule.append({
            "task": name,
            "start": current_start,
            "duration": duration,
            "end": end
        })
        current_start = next_workday(end)
    overall_end = schedule[-1]["end"]
    return schedule, overall_end

# ====== UI 기능들 ======
def on_generate_commit():
    jira = jira_entry.get().strip()
    message = message_entry.get().strip()
    if not jira:
        messagebox.showwarning("입력 오류", "JIRA 티켓 번호를 입력하세요.")
        return
    commit_msg, branch_name, switch1_name, switch2_name  = generate_commit_and_branch(jira, message)
    commit_output.config(state="normal")
    commit_output.delete(1.0, tk.END)
    commit_output.insert(tk.END, commit_msg)
    branch_output.config(state="normal")
    branch_output.delete(0, tk.END)
    branch_output.insert(0, branch_name)
    switch1_output.config(state="normal")
    switch1_output.delete(0, tk.END)
    switch1_output.insert(0, switch1_name)
    switch2_output.config(state="normal")
    switch2_output.delete(0, tk.END)
    switch2_output.insert(0, switch2_name)

def on_generate_schedule(start_date_str):
    raw_text = schedule_input.get("1.0", tk.END).strip()
    try:
        # 시작일 파싱
        datetime.strptime(start_date_str, "%Y-%m-%d")  # 유효성 체크만
        tasks = []
        for line in raw_text.splitlines():
            if line:
                name, days = line.split(",")
                tasks.append((name.strip(), int(days.strip())))
        schedule, final_end = generate_schedule_with_holidays(tasks, start_date_str)
        total_days = sum(task["duration"] for task in schedule)

        schedule_output.config(state="normal")
        schedule_output.delete("1.0", tk.END)
        schedule_output.insert(tk.END, f"📅 시작일 기준: {start_date_str}\n\n")
        for task in schedule:
            schedule_output.insert(tk.END, f"{task['task']: <10} | {task['start'].date()} → {task['end'].date()} | {task['duration']}일\n")
        schedule_output.insert(tk.END, f"\n📌 총 워킹데이: {total_days}\n📌 최종 완료일: {final_end.date()}")
        next_day = next_workday(final_end)
        schedule_output.insert(tk.END, f"\n📌 다음 워킹데이: {next_day.date()}")
        schedule_output.config(state="disabled")
        
    except ValueError:
        messagebox.showerror("입력 오류", "시작일 형식이 잘못되었습니다.\n예: 2025-05-27")
    except Exception as e:
        messagebox.showerror("입력 오류", f"작업 입력 형식이 잘못되었습니다:\n\n{e}")


# ====== UI 시작 ======
root = tk.Tk()
root.title("개발 도우미 툴")

tab_control = ttk.Notebook(root)

# --- Tab 1: 커밋 생성기 ---
commit_tab = tk.Frame(tab_control)
tab_control.add(commit_tab, text="커밋 생성기")

tk.Label(commit_tab, text="JIRA 티켓 번호").grid(row=0, column=0, sticky="e")
jira_entry = tk.Entry(commit_tab, width=40)
jira_entry.grid(row=0, column=1)

tk.Label(commit_tab, text="커밋 메시지").grid(row=1, column=0, sticky="e")
message_entry = tk.Entry(commit_tab, width=40)
message_entry.grid(row=1, column=1)

tk.Button(commit_tab, text="생성", command=on_generate_commit).grid(row=2, column=0, pady=10)
tk.Button(commit_tab, text="닫기", command=root.quit).grid(row=2, column=1, pady=10)

# 커밋 메시지
tk.Label(commit_tab, text="커밋 메시지:").grid(row=3, column=0, sticky="ne")
commit_output = tk.Text(commit_tab, height=3, width=60)
commit_output.grid(row=3, column=1)
tk.Button(commit_tab, text="복사", command=lambda: copy_text_from_widget(commit_output)).grid(row=3, column=2)

# 브랜치 이름
tk.Label(commit_tab, text="브랜치 이름:").grid(row=4, column=0, sticky="e")
branch_output = tk.Entry(commit_tab, width=60)
branch_output.grid(row=4, column=1)
tk.Button(commit_tab, text="복사", command=lambda: copy_text_from_widget(branch_output)).grid(row=4, column=2)

# 스위치1
tk.Label(commit_tab, text="스위치1:").grid(row=5, column=0, sticky="e")
switch1_output = tk.Entry(commit_tab, width=60)
switch1_output.grid(row=5, column=1)
tk.Button(commit_tab, text="복사", command=lambda: copy_text_from_widget(switch1_output)).grid(row=5, column=2)

# 스위치2
tk.Label(commit_tab, text="스위치2:").grid(row=6, column=0, sticky="e")
switch2_output = tk.Entry(commit_tab, width=60)
switch2_output.grid(row=6, column=1)
tk.Button(commit_tab, text="복사", command=lambda: copy_text_from_widget(switch2_output)).grid(row=6, column=2)


# --- Tab 2: 케이스 변환기 ---
case_labels = {}
case_tab = tk.Frame(tab_control)
tab_control.add(case_tab, text="케이스 변환기")

tk.Label(case_tab, text="입력 문자열").grid(row=0, column=0, sticky="e")
case_input = tk.Entry(case_tab, width=50)
case_input.grid(row=0, column=1, padx=5)

tk.Button(case_tab, text="변환", command=lambda: update_case_outputs(case_input.get())).grid(row=0, column=2)


# --- Tab 3: 일정 계산기 ---
schedule_tab = tk.Frame(tab_control)
tab_control.add(schedule_tab, text="일정 계산기")

# 시작일 입력
tk.Label(schedule_tab, text="시작일 (YYYY-MM-DD)").grid(row=0, column=0, sticky="e")
start_date_entry = tk.Entry(schedule_tab, width=20)
start_date_entry.insert(0, "2025-05-27")
start_date_entry.grid(row=0, column=1, sticky="w")

# 작업 목록 입력
tk.Label(schedule_tab, text="작업 목록 입력\n(작업명, 일수)").grid(row=1, column=0, sticky="ne")
schedule_input = tk.Text(schedule_tab, height=8, width=40)
schedule_input.insert("1.0", "요구사항 분석, 3\n설계, 4\n구현, 10\n테스트, 5")
schedule_input.grid(row=1, column=1)

tk.Button(schedule_tab, text="계산", command=lambda: on_generate_schedule(start_date_entry.get())).grid(row=2, column=0, pady=10)

schedule_output = tk.Text(schedule_tab, height=12, width=60, state="disabled")
schedule_output.grid(row=2, column=1)



tab_control.pack(expand=1, fill="both")
root.mainloop()
