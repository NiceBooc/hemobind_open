# HemoBind GUI — Полный план приложения
# Документ для LLM-агентов, которые будут реализовывать приложение.
# READ THIS ENTIRE FILE BEFORE WRITING ANY CODE.

---

## 1. КОНЦЕПЦИЯ

Настольное GUI-приложение **HemoBind GUI** поверх существующего CLI-пакета `hemobind`.
Принцип: GUI — тонкая оболочка над уже работающим кодом в `hemobind/stages/`.
**НЕ переписывать бизнес-логику — только обернуть в UI.**

---

## 2. ТЕХНОЛОГИЧЕСКИЙ СТЕК

| Компонент | Выбор | Причина |
|-----------|-------|---------|
| GUI фреймворк | **PySide6** | LGPL, официальный Qt binding |
| Тема | **pyqtdarktheme** (`pip install pyqtdarktheme`) | Современный flat dark theme |
| Логи в UI | `QThread` + Signal/Slot | Thread-safe вывод |
| Конфиг | YAML + существующий `hemobind.config` | Не дублировать |
| Визуализация | `pyqtgraph` (опционально, для энергий) | Высокая производительность |

```bash
pip install PySide6 pyqtdarktheme pyyaml
# опционально:
pip install pyqtgraph
```

---

## 3. СТРУКТУРА ДИРЕКТОРИЙ

```
hemobind/
├── hemobind/          # существующий CLI-пакет (НЕ ТРОГАТЬ)
│   ├── stages/        # s1_prepare.py ... s7_md.py
│   ├── utils/
│   ├── config.py
│   └── pipeline.py
│
└── hemobind_gui/      # НОВЫЙ пакет — только GUI
    ├── __init__.py
    ├── main.py                    # точка входа: python -m hemobind_gui
    ├── app.py                     # QApplication setup, theme
    │
    ├── core/
    │   ├── __init__.py
    │   ├── worker.py              # PipelineWorker(QThread) — запуск pipeline
    │   ├── dependency_checker.py  # проверка naличия obabel, adgpu, docker, schrodinger
    │   ├── session.py             # сохранение/восстановление сессии (JSON)
    │   └── log_handler.py        # QLoggingHandler → Signal → UI
    │
    ├── widgets/
    │   ├── __init__.py
    │   ├── main_window.py         # MainWindow(QMainWindow) — каркас
    │   ├── stage_panel.py         # StagePanel — базовый класс панели этапа
    │   ├── panels/
    │   │   ├── __init__.py
    │   │   ├── p1_prepare.py      # PreparePanel
    │   │   ├── p2_docking.py      # DockingPanel
    │   │   ├── p3_analyze.py      # AnalyzePanel
    │   │   ├── p4_select.py       # SelectPanel
    │   │   ├── p5_prepwiz.py      # PrepwizPanel
    │   │   ├── p6_build.py        # BuildPanel
    │   │   └── p7_md.py           # MDPanel
    │   ├── console_widget.py      # ConsoleWidget — цветной вывод логов
    │   ├── pipeline_view.py       # PipelineView — визуальная цепочка этапов
    │   ├── file_input.py          # FileInputWidget — поле + кнопка Browse
    │   ├── settings_dialog.py     # SettingsDialog — пути к инструментам
    │   └── run_control.py         # RunControlWidget — кнопки Run/Pause/Stop
    │
    └── resources/
        ├── styles/
        │   └── extra.qss          # дополнительные стили поверх qdarktheme
        └── icons/                 # SVG иконки для этапов
```

---

## 4. ГЛАВНОЕ ОКНО (main_window.py)

### 4.1 Layout

```
┌─────────────────────────────────────────────────────────────────┐
│ MenuBar: File | Run | Tools | Help                              │
├──────────────────┬──────────────────────────────────────────────┤
│  LEFT SIDEBAR    │              CENTRAL AREA                    │
│  (300px fixed)   │                                              │
│                  │  ┌──────────────────────────────────────┐   │
│  Pipeline View:  │  │   Stage Config Panel (QStackedWidget) │   │
│  ● S1 Prepare ✓  │  │   Показывает настройки выбранного    │   │
│  ● S2 Docking ▶  │  │   этапа. При клике на этап в         │   │
│  ○ S3 PLIP       │  │   PipelineView — переключается.       │   │
│  ○ S4 Select     │  └──────────────────────────────────────┘   │
│  ○ S5 PrepWiz    │                                              │
│  ○ S6 Build      │  ┌──────────────────────────────────────┐   │
│  ○ S7 MD         │  │   Run Control                         │   │
│                  │  │  [▶ Run] [⏸ Pause] [■ Stop]          │   │
│  ──────────────  │  │  From: [S1▼]  To: [S7▼]              │   │
│  Dependency      │  │  Progress: ████░░░░ 3/7               │   │
│  Status:         │  └──────────────────────────────────────┘   │
│  ✓ obabel        │                                              │
│  ✓ adgpu         ├──────────────────────────────────────────────┤
│  ✓ docker        │   BOTTOM DOCK: Console (resizable)          │
│  ✗ schrodinger   │   [INFO][WARN][ERROR] фильтры | [Clear]     │
│                  │   01:14:30 [INFO] [S1] Stripping receptor..  │
│  [⚙ Settings]   │   01:14:31 [DONE] s1_prepare               │
└──────────────────┴──────────────────────────────────────────────┘
```

### 4.2 Dock Widgets
- **Left Dock**: `PipelineView` + `DependencyStatus` — фиксирован слева
- **Bottom Dock**: `ConsoleWidget` — перетаскиваемый, закрываемый
- **Central**: `QStackedWidget` со Stage Config Panels + `RunControlWidget`

---

## 5. PIPELINE VIEW (pipeline_view.py)

`QWidget` с кастомной отрисовкой (`paintEvent`):

```
[S1] ──→ [S2] ──→ [S3] ──→ [S4] ──→ [S5] ──→ [S6] ──→ [S7]
Prep    Dock    PLIP    Select  PrepWiz  Build    MD
 ✓       ▶       ○       ○       ○        ○       ○
```

Состояния этапа:
- `IDLE` — серый кружок
- `RUNNING` — синий пульсирующий (QPropertyAnimation)
- `DONE` — зелёный с галочкой
- `FAILED` — красный с крестом
- `SKIPPED` — серый с чертой

Клик на этап — выбирает его (показывает Config Panel в центре).
Двойной клик — открывает его вывод в консоли.

---

## 6. STAGE CONFIG PANELS

### Базовый класс `StagePanel(QWidget)`:
```python
class StagePanel(QWidget):
    config_changed = Signal(dict)  # emit при изменении любого поля
    
    def get_config(self) -> dict:  # возвращает dict с настройками
        raise NotImplementedError
    
    def set_config(self, cfg: dict):  # загружает настройки в UI
        raise NotImplementedError
    
    def validate(self) -> list[str]:  # возвращает список ошибок
        raise NotImplementedError
```

### Панели по этапам:

#### P1 — Prepare
```
Receptor PDB:  [_____________] [Browse]
Ligands:       [_____________] [Browse] [+Add] [-Remove]
               список mol2/sdf файлов
Grid Mode:     ○ Blind  ● Targeted
  If targeted:
    Center X/Y/Z: [__] [__] [__]
    Size X/Y/Z:   [__] [__] [__]
Output dir:    [_____________] [Browse]
```

#### P2 — Docking
```
Tool:          ○ AutoDock-GPU  ○ Vina
N Runs:        [100      ]
N Poses:       [10       ]
Exhaustiveness:[32       ]  (Vina only)
adgpu path:    [auto-detect] [Browse]
```

#### P3 — PLIP Analysis
```
Docker Image:  [pharmai/plip  ]
  [Test Docker Connection]  ✓ OK / ✗ Failed
Top N poses:   [3        ]
```

#### P4 — Select
```
Scoring weights:
  Energy:       [-1.0    ]
  H-bonds:      [+0.5    ]
  Hydrophobic:  [+0.3    ]
Cluster radius: [3.0 Å   ]
Top N select:   [2       ]
```

#### P5 — PrepWizard
```
Schrodinger:   [/opt/schrodinger2025-2] [Browse]
pH:            [7.0     ]
Fill side chains: [✓]
Fix:           [✓]
Parallel jobs: [2       ]
```

#### P6 — System Builder
```
Water model:   [TIP3P    ▼]
Box buffer:    [15.0 Å   ]
Salt conc:     [0.15 mol/L]
Parallel jobs: [2        ]
```

#### P7 — MD
```
Sim time:      [100.0 ns ]
GPU index:     [0        ]
Schrodinger:   [/opt/schrodinger2025-2] [Browse]
  (наследует из P5 автоматически)
MSJ Protocol:
  ● Standard (7-stage equilibration)
  ○ Custom [Browse .msj]
```

---

## 7. CONSOLE WIDGET (console_widget.py)

`QTextEdit` (ReadOnly) с цветной подсветкой:

```python
COLORS = {
    "INFO":    "#a8d8a8",   # зеленоватый
    "WARNING": "#f4d03f",   # жёлтый
    "ERROR":   "#e74c3c",   # красный
    "DEBUG":   "#7f8c8d",   # серый
    "DONE":    "#2ecc71",   # яркий зелёный
    "START":   "#3498db",   # синий
}
```

Фильтры (QCheckBox в тулбаре консоли):
- `☑ INFO` `☑ WARN` `☑ ERROR` `☐ DEBUG`

Кнопки: `[Clear]` `[Save Log]` `[Copy]`

Ввод команд: строка `QLineEdit` внизу — для будущего интерактивного режима.

**Реализация capture логов:**
```python
class LogHandler(logging.Handler):
    def __init__(self, signal):
        super().__init__()
        self._signal = signal
    
    def emit(self, record):
        msg = self.format(record)
        self._signal.emit(record.levelname, msg)
```

---

## 8. WORKER THREAD (worker.py)

```python
class PipelineWorker(QThread):
    log_message   = Signal(str, str)  # level, message
    stage_started = Signal(str)       # stage_id
    stage_done    = Signal(str)       # stage_id
    stage_failed  = Signal(str, str)  # stage_id, error
    progress      = Signal(int, int)  # current, total
    finished      = Signal(bool)      # success

    def __init__(self, config: HemobindConfig, run_dir: Path,
                 from_stage: str | None, to_stage: str | None):
        ...

    def run(self):
        # Перехватывает logging, запускает Pipeline
        pipeline = Pipeline(self.config, self.run_dir)
        pipeline.run(self.from_stage, self.to_stage)
    
    def stop(self):
        self._stop_event.set()
```

**Важно**: `Pipeline.run()` блокирующий. Worker запускает его в отдельном потоке. Для остановки — `threading.Event` + проверка в `wait_for_job`.

---

## 9. DEPENDENCY CHECKER (dependency_checker.py)

```python
TOOLS = {
    "obabel":      {"cmd": ["obabel", "--version"], "required": True},
    "adgpu":       {"cmd": ["adgpu", "--version"],  "required": True},
    "autogrid4":   {"cmd": ["autogrid4"],            "required": True},
    "docker":      {"cmd": ["docker", "info"],       "required": True},
    "schrodinger": {"path_key": "md.schrodinger",    "required": False},
    "prepwizard":  {"subpath": "utilities/prepwizard","required": False},
}

def check_all(config: HemobindConfig) -> dict[str, CheckResult]:
    # возвращает {tool: CheckResult(ok=bool, version=str, message=str)}
    ...
```

**В UI** — виджет `DependencyStatusWidget`:
- Зелёная галочка / красный крест рядом с каждым инструментом
- При красном — кнопка `[Fix]` или `[Set Path]` → открывает `SettingsDialog`
- `[Re-check]` кнопка для повторной проверки

---

## 10. SETTINGS DIALOG (settings_dialog.py)

```
┌─ Settings ──────────────────────────────────────────┐
│ Tool Paths                                           │
│ ┌─────────────────────────────────────────────────┐ │
│ │ Schrodinger: [/opt/schrodinger2025-2  ] [Browse]│ │
│ │ AutoDock-GPU:[/usr/local/bin/adgpu    ] [Browse]│ │
│ │ AutoGrid4:  [/usr/local/bin/autogrid4] [Browse]│ │
│ │ Docker:     [/usr/bin/docker          ] [Browse]│ │
│ │ OBabel:     [/usr/bin/obabel          ] [Browse]│ │
│ └─────────────────────────────────────────────────┘ │
│ Appearance                                           │
│   Theme: ● Dark  ○ Light                            │
│   Font size: [11 px]                                │
│ Logging                                             │
│   Level: [DEBUG▼]                                   │
│   Max lines: [10000  ]                              │
│                          [Cancel]  [Save & Apply]   │
└─────────────────────────────────────────────────────┘
```

Настройки сохраняются в `~/.config/hemobind/settings.json`.

---

## 11. RUN CONTROL (run_control.py)

```python
class RunControlWidget(QWidget):
    run_requested  = Signal(str, str)  # from_stage, to_stage
    stop_requested = Signal()
    
    # UI:
    # From: [S1 ▼]  To: [S7 ▼]  [▶ Run Full] [▶ Run Stage] [■ Stop]
    # ProgressBar + текущий этап лейбл
```

---

## 12. SESSION MANAGEMENT (session.py)

Сессия = набор настроек всех панелей + путь к run_dir.
Сохраняется как JSON в `~/.config/hemobind/last_session.json`.

```python
class Session:
    def save(self, path: Path, panels_config: dict, run_dir: str): ...
    def load(self, path: Path) -> dict: ...
    def list_recent(self) -> list[dict]: ...  # File → Recent Sessions
```

**File → New Session** — сброс всех полей.
**File → Open Session** — загрузить JSON.
**File → Recent** — последние 5 сессий.

---

## 13. МЕНЮ

```
File
  New Session          Ctrl+N
  Open Session...      Ctrl+O
  Save Session         Ctrl+S
  Save Session As...
  ──────────────────
  Recent Sessions →
  ──────────────────
  Exit                 Ctrl+Q

Run
  Run Full Pipeline    F5
  Run from Stage →
  Stop                 Ctrl+C (в контексте Run)
  ──────────────────
  Open Run Directory

Tools
  Check Dependencies
  Settings...          Ctrl+,
  Clear Run Cache

Help
  Documentation
  Report Issue
  About HemoBind
```

---

## 14. ЦВЕТОВАЯ СХЕМА

Тема: `qdarktheme.setup_theme("dark")` + кастомный QSS:

```qss
/* extra.qss */

/* Панели этапов */
StagePanel {
    background: #1e2130;
    border: 1px solid #2d3250;
    border-radius: 8px;
    padding: 12px;
}

/* Статус этапа в PipelineView */
.stage-done    { color: #2ecc71; }
.stage-running { color: #3498db; }
.stage-failed  { color: #e74c3c; }
.stage-idle    { color: #7f8c8d; }

/* Консоль */
ConsoleWidget QTextEdit {
    background: #0d1117;
    font-family: "JetBrains Mono", "Fira Code", monospace;
    font-size: 11px;
}

/* FileInputWidget */
FileInputWidget QLineEdit {
    background: #252836;
    border: 1px solid #3d4166;
    border-radius: 4px;
    padding: 4px 8px;
}
FileInputWidget QLineEdit:focus {
    border-color: #5c7cfa;
}
```

---

## 15. КЛЮЧЕВЫЕ ПАТТЕРНЫ РЕАЛИЗАЦИИ

### 15.1 FileInputWidget (используется везде)
```python
class FileInputWidget(QWidget):
    path_changed = Signal(str)
    
    def __init__(self, label: str, mode: str = "file",
                 filter: str = "All Files (*)", parent=None):
        # mode = "file" | "dir"
        # QLabel + QLineEdit + QPushButton("Browse")
        ...
```

### 15.2 Запуск pipeline
```python
# В MainWindow:
def on_run_clicked(self, from_stage, to_stage):
    config = self._build_config_from_panels()
    errors = self._validate_all_panels()
    if errors:
        QMessageBox.warning(self, "Validation Errors", "\n".join(errors))
        return
    
    self.worker = PipelineWorker(config, run_dir, from_stage, to_stage)
    self.worker.log_message.connect(self.console.append_message)
    self.worker.stage_started.connect(self.pipeline_view.set_running)
    self.worker.stage_done.connect(self.pipeline_view.set_done)
    self.worker.stage_failed.connect(self.pipeline_view.set_failed)
    self.worker.finished.connect(self.on_pipeline_finished)
    self.worker.start()
```

### 15.3 Интеграция с существующим logging
```python
# В worker.run():
handler = LogHandler(self.log_message)
handler.setFormatter(logging.Formatter("%(asctime)s [%(levelname)s] %(message)s"))
logging.getLogger("hemobind").addHandler(handler)
try:
    pipeline.run(self.from_stage, self.to_stage)
finally:
    logging.getLogger("hemobind").removeHandler(handler)
```

---

## 16. ПОРЯДОК РЕАЛИЗАЦИИ ДЛЯ LLM-АГЕНТОВ

### Шаг 1 — Каркас (без логики)
1. `hemobind_gui/__init__.py` + `main.py` + `app.py`
2. `MainWindow` с пустыми dock-панелями
3. `ConsoleWidget` (только отображение, без worker)
4. Убедиться, что окно открывается с темой

### Шаг 2 — Утилиты
5. `FileInputWidget`
6. `SettingsDialog` + `settings.json` save/load
7. `DependencyChecker` + `DependencyStatusWidget`

### Шаг 3 — Stage Panels
8. Базовый `StagePanel`
9. `P1PreparePanel` через `P7MDPanel` (по одному)
10. `PipelineView` (кастомная отрисовка)
11. `QStackedWidget` в центре — переключение при клике на PipelineView

### Шаг 4 — Запуск
12. `PipelineWorker(QThread)` + `LogHandler`
13. `RunControlWidget`
14. Соединение сигналов: Worker → PipelineView + Console

### Шаг 5 — Полировка
15. `Session` + меню File
16. Анимация состояний в PipelineView
17. Иконки + финальный QSS

---

## 17. ЗАВИСИМОСТИ (pyproject.toml дополнение)

```toml
[project.optional-dependencies]
gui = [
    "PySide6>=6.6.0",
    "pyqtdarktheme>=2.1.0",
    "pyqtgraph>=0.13.0",   # опционально, для графиков энергий
]

[project.scripts]
hemobind     = "hemobind.cli:main"
hemobind-gui = "hemobind_gui.main:main"
```

---

## 18. КРИТИЧЕСКИЕ ЗАМЕЧАНИЯ (НЕ ЗАБЫТЬ)

1. **НЕ ВЫЗЫВАТЬ** методы QWidget из QThread — только через Signal.
2. **Pipeline.run() блокирующий** — всегда в отдельном потоке.
3. `wait_for_job` в s7_md.py использует `time.sleep` — добавить проверку stop_event.
4. Шредингер-утилиты **долго стартуют** (~10-30с) — не зависать на них без индикатора.
5. `context.json` — механизм resume уже реализован, GUI должен это использовать.
6. Все пути в настройках — абсолютные, проверять `Path.exists()` перед запуском.
7. Docker может требовать `sudo` — предупреждать пользователя, если `docker info` упал.
8. При большом stdout (autogrid4 карты) — **буферизовать** вывод, не обновлять QTextEdit на каждый символ.

---

## 19. ФАЙЛ ТОЧКИ ВХОДА (main.py)

```python
#!/usr/bin/env python3
"""HemoBind GUI — Molecular Docking & MD Pipeline"""
import sys

def main():
    from PySide6.QtWidgets import QApplication
    import qdarktheme
    
    app = QApplication(sys.argv)
    app.setApplicationName("HemoBind")
    app.setOrganizationName("HemoBind")
    app.setStyle("Fusion")
    qdarktheme.setup_theme("dark")
    
    # Загрузить extra.qss
    from importlib.resources import files
    qss = files("hemobind_gui.resources.styles").joinpath("extra.qss").read_text()
    app.setStyleSheet(app.styleSheet() + qss)
    
    from hemobind_gui.widgets.main_window import MainWindow
    window = MainWindow()
    window.show()
    
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
```
