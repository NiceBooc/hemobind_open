# HemoBind GUI — Agent Implementation Instructions
# Для LLM-агента, который будет ПИСАТЬ КОД приложения.
# Это рабочий документ: прочти, выполни шаги по порядку, отмечай прогресс.

---

## КОНТЕКСТ

Ты будешь строить GUI-оболочку для CLI-пакета `hemobind`.
Весь бизнес-код уже работает в `/home/qweqwe/AntiG/hemobind/hemobind/`.
Твоя задача — **только GUI**, не трогай `hemobind/`.

Полный план архитектуры: `/home/qweqwe/AntiG/hemobind/GUI_PLAN.md`
Прочти его целиком ДО начала кодирования.

---

## СРЕДА

```bash
# Активировать venv
source /home/qweqwe/AntiG/Docking/venv/bin/activate

# Установить GUI зависимости
pip install PySide6 pyqtdarktheme

# Рабочая директория
cd /home/qweqwe/AntiG/hemobind/

# Запуск GUI для тестирования
python -m hemobind_gui
```

---

## ЭТАПЫ (отмечай [x] по завершении)

- [ ] Шаг 1: Каркас — `hemobind_gui/` + `MainWindow` с пустыми панелями
- [ ] Шаг 2: `ConsoleWidget` — цветной вывод логов
- [ ] Шаг 3: `FileInputWidget` + `SettingsDialog`
- [ ] Шаг 4: `DependencyChecker` + UI-виджет статуса
- [ ] Шаг 5: `P1PreparePanel` через `P7MDPanel`
- [ ] Шаг 6: `PipelineView` — визуальная цепочка с состояниями
- [ ] Шаг 7: `PipelineWorker(QThread)` + `LogHandler`
- [ ] Шаг 8: `RunControlWidget` + подключение сигналов
- [ ] Шаг 9: `Session` + меню
- [ ] Шаг 10: Финальный QSS + анимации

---

## ПРАВИЛА

1. Тестируй каждый шаг запуском `python -m hemobind_gui` — окно должно открываться
2. НИКОГДА не вызывай методы QWidget из QThread
3. Используй `PySide6`, не `PyQt6` (разные import-пути)
4. `qdarktheme.setup_theme("dark")` вызывать ДО создания MainWindow
5. Если что-то не работает — смотри консоль Python (stderr), не GUI-консоль
