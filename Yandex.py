import sys
from PyQt6.QtWidgets import (
    QApplication,
    QWidget,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QHBoxLayout,
    QGridLayout,
    QComboBox,
    QLineEdit,
    QDateEdit,
    QTimeEdit,
    QMessageBox,
    QTabWidget,
    QTableWidget,
    QTableWidgetItem,
    QMainWindow,
    QDialog,
    QSpacerItem,
    QSpinBox,
    QScrollArea,
    QInputDialog,
)
from PyQt6.QtCore import Qt, pyqtSignal, QDate, QTime, QEvent, QTimer
import sqlite3
import datetime
from plyer import notification


class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Приложение для лекарств")
        self.setGeometry(100, 100, 600, 400)


        self.conn = sqlite3.connect("medicines.db")
        self.cursor = self.conn.cursor()


        self.cursor.execute('''
          CREATE TABLE IF NOT EXISTS medicines (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            dosage TEXT,
            date TEXT,
            time TEXT
          )
        ''')

        self.cursor.execute('''
          CREATE TABLE IF NOT EXISTS inventory (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            quantity INTEGER
          )
        ''')


        self.cursor.execute('''
          CREATE TABLE IF NOT EXISTS medicines_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            dosage TEXT,
            date TEXT,
            time TEXT,
            received_time TEXT,
            description TEXT
          )
        ''')

        self.conn.commit()

        welcome_label = QLabel(
            "Добро пожаловать в приложение для управления лекарствами"
        )

        add_medicine_button = QPushButton("Добавить лекарство")
        add_medicine_button.clicked.connect(self.open_add_medicine_window)
        schedule_button = QPushButton("График приема")
        schedule_button.clicked.connect(self.open_schedule_window)
        inventory_button = QPushButton("Запасы лекарств")
        inventory_button.clicked.connect(self.open_inventory_window)
        add_inventory_button = QPushButton("Добавить запас")
        add_inventory_button.clicked.connect(self.open_add_inventory_window)
        self.log_button = QPushButton("Журнал приема")
        self.log_button.clicked.connect(self.open_log_window)
        help_button = QPushButton("Помощь")
        help_button.clicked.connect(self.open_help_window)

        layout = QVBoxLayout()
        layout.addWidget(welcome_label)
        layout.addWidget(add_medicine_button)
        layout.addWidget(schedule_button)
        layout.addWidget(add_inventory_button)
        layout.addWidget(inventory_button)
        layout.addWidget(self.log_button)
        layout.addWidget(help_button)
        self.setLayout(layout)

        self.installEventFilter(self)

    def open_add_medicine_window(self):
        self.add_medicine_window = AddMedicineWindow(self)
        self.add_medicine_window.show()

    def open_schedule_window(self):
        self.schedule_window = ScheduleWindow(self)
        self.schedule_window.show()

    def open_inventory_window(self):
        self.inventory_window = InventoryWindow(self)
        self.inventory_window.show()

    def open_add_inventory_window(self):
        self.add_inventory_window = AddInventoryWindow(self)
        self.add_inventory_window.show()

    def open_help_window(self):
        self.help_window = HelpWindow()
        self.help_window.show()

    def open_log_window(self):
        self.log_window = LogWindow(self)
        self.log_window.show()

    def get_medicine_history(self):
        self.cursor.execute(
            "SELECT DISTINCT name FROM medicines UNION SELECT DISTINCT name FROM medicines_log")
        medicine_names = [row[0] for row in self.cursor.fetchall()]
        return sorted(medicine_names)

    def eventFilter(self, watched: 'QObject', event: 'QEvent') -> bool:
        if event.type() == QEvent.Type.KeyPress and event.key() == Qt.Key.Key_D:
            if QMessageBox.question(
                    self,
                    "Сброс данных",
                    "Вы уверены, что хотите сбросить все данные?",
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                    QMessageBox.StandardButton.No,
            ) == QMessageBox.StandardButton.Yes:
                self.reset_data()
        return super().eventFilter(watched, event)

    def reset_data(self):

        self.cursor.execute("DELETE FROM medicines")

        self.cursor.execute("DELETE FROM inventory")
        self.cursor.execute("DELETE FROM medicines_log")
        self.conn.commit()
        QMessageBox.information(self, "Сброс данных",
                                "Все данные успешно сброшены")


class AddMedicineWindow(QWidget):
    def __init__(self, main_window):
        super().__init__()
        self.setWindowTitle("Добавить лекарство")
        self.setGeometry(100, 100, 300, 200)
        self.main_window = main_window

        self.medicine_history = self.main_window.get_medicine_history()

        medicine_label = QLabel("Лекарство:")
        self.medicine_combobox = QComboBox()
        self.medicine_combobox.addItems(sorted(
            self.medicine_history))
        self.medicine_combobox.setEditable(True)  
        dosage_label = QLabel("Дозировка:")
        self.dosage_edit = QLineEdit()
        self.dosage_edit.setPlaceholderText("Введите дозировку")
        date_label = QLabel("Дата:")
        self.date_edit = QDateEdit()
        self.date_edit.setDate(QDate.currentDate())
        time_label = QLabel("Время:")
        self.time_edit = QTimeEdit()
        self.time_edit.setTime(QTime.currentTime())

        save_button = QPushButton("Сохранить")
        save_button.clicked.connect(self.save_medicine)

        layout = QGridLayout()
        layout.addWidget(medicine_label, 0, 0)
        layout.addWidget(self.medicine_combobox, 0, 1)
        layout.addWidget(dosage_label, 1, 0)
        layout.addWidget(self.dosage_edit, 1, 1)
        layout.addWidget(date_label, 2, 0)
        layout.addWidget(self.date_edit, 2, 1)
        layout.addWidget(time_label, 3, 0)
        layout.addWidget(self.time_edit, 3, 1)
        layout.addWidget(save_button, 4, 0, 1, 2)
        self.setLayout(layout)

    def save_medicine(self):
        medicine_name = self.medicine_combobox.currentText()
        dosage = self.dosage_edit.text()
        date = self.date_edit.date().toString("yyyy-MM-dd")
        time = self.time_edit.time().toString("HH:mm")
        if medicine_name and dosage:

            try:
                float(dosage) 
            except ValueError:
                QMessageBox.warning(self, "Ошибка",
                                    "Дозировка должна быть числом")
                return 

            current_datetime = datetime.datetime.now()

            entered_datetime = datetime.datetime.strptime(date + " " + time,
                                                          "%Y-%m-%d %H:%M")

            if entered_datetime >= current_datetime:
                self.main_window.cursor.execute(
                    "INSERT INTO medicines (name, dosage, date, time) VALUES (?, ?, ?, ?)",
                    (medicine_name, dosage, date, time),
                )
                self.main_window.conn.commit()
                self.close()
            else:
                QMessageBox.warning(self, "Ошибка",
                                    "Время приема не может быть раньше текущего времени")
        else:

            QMessageBox.warning(self, "Ошибка",
                                "Введите название лекарства и дозировку")


class ScheduleWindow(QWidget):
    def __init__(self, main_window):
        super().__init__()
        self.setWindowTitle("График приема")
        self.setGeometry(100, 100, 400, 300)
        self.main_window = main_window
        self.selected_row = None


        self.schedule_table = QTableWidget()
        self.schedule_table.setColumnCount(4)
        self.schedule_table.setHorizontalHeaderLabels(
            ["Лекарство", "Дозировка", "Дата", "Время"])
        self.schedule_table.setSelectionBehavior(
            QTableWidget.SelectionBehavior.SelectRows)
        self.schedule_table.setSelectionMode(
            QTableWidget.SelectionMode.SingleSelection)


        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText("Поиск...")
        self.search_edit.textChanged.connect(self.search_schedule)


        self.delete_button = QPushButton("Удалить")
        self.delete_button.clicked.connect(self.delete_medicine)
        self.edit_button = QPushButton("Изменить")
        self.edit_button.clicked.connect(self.edit_medicine)
        self.repeat_button = QPushButton("Повторить")
        self.repeat_button.clicked.connect(self.open_repeat_dialog)
        self.repeat_button.setEnabled(False)
        self.delete_button.setEnabled(False)
        self.edit_button.setEnabled(False)


        layout = QVBoxLayout()
        layout.addWidget(self.search_edit)
        layout.addWidget(self.schedule_table)
        button_layout = QHBoxLayout()
        button_layout.addWidget(self.delete_button)
        button_layout.addWidget(self.edit_button)
        button_layout.addWidget(self.repeat_button)
        layout.addLayout(button_layout)
        self.setLayout(layout)


        self.schedule_table.selectionModel().selectionChanged.connect(
            self.handle_selection_changed)

        self.update_table()

    def update_table(self):
        self.schedule_table.setRowCount(0)
        self.main_window.cursor.execute(
            "SELECT * FROM medicines ORDER BY date ASC, time ASC"
        )
        medicines = self.main_window.cursor.fetchall()

        for i, medicine in enumerate(medicines):
            self.schedule_table.insertRow(i)
            self.schedule_table.setItem(i, 0, QTableWidgetItem(medicine[1]))
            self.schedule_table.setItem(i, 1, QTableWidgetItem(medicine[2]))
            self.schedule_table.setItem(i, 2, QTableWidgetItem(medicine[3]))
            self.schedule_table.setItem(i, 3, QTableWidgetItem(medicine[4]))

            self.schedule_table.item(i, 0).setData(Qt.ItemDataRole.UserRole,
                                                   medicine[0])

    def delete_medicine(self):
        selected_rows = self.schedule_table.selectionModel().selectedRows()
        if selected_rows:
            row = selected_rows[0].row()

            if QMessageBox.question(
                    self,
                    "Удаление",
                    "Вы уверены, что хотите удалить это событие?",
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                    QMessageBox.StandardButton.No,
            ) == QMessageBox.StandardButton.Yes:

                medicine_id = self.schedule_table.item(row, 0).data(
                    Qt.ItemDataRole.UserRole)

                self.main_window.cursor.execute(
                    "DELETE FROM medicines WHERE id = ?", (medicine_id,))
                self.main_window.conn.commit()

                self.update_table()

    def edit_medicine(self):
        selected_rows = self.schedule_table.selectionModel().selectedRows()
        if selected_rows:
            row = selected_rows[0].row()

            medicine_id = self.schedule_table.item(row, 0).data(
                Qt.ItemDataRole.UserRole)

            self.main_window.cursor.execute(
                "SELECT * FROM medicines WHERE id = ?", (medicine_id,))
            medicine = self.main_window.cursor.fetchone()

            self.edit_dialog = EditMedicineDialog(medicine, self.main_window)
            self.edit_dialog.setWindowTitle("Редактировать событие")

            self.edit_dialog.data_changed.connect(self.update_data)

            self.edit_dialog.show()

    def update_data(self, medicine_data):

        selected_rows = self.schedule_table.selectionModel().selectedRows()
        if selected_rows:
            row = selected_rows[0].row()

            medicine_id = self.schedule_table.item(row, 0).data(
                Qt.ItemDataRole.UserRole)
            self.main_window.cursor.execute(
                "UPDATE medicines SET name = ?, dosage = ?, date = ?, time = ? WHERE id = ?",
                (
                    medicine_data["name"],
                    medicine_data["dosage"],
                    medicine_data["date"],
                    medicine_data["time"],
                    medicine_id,
                ),
            )
            self.main_window.conn.commit()
            self.update_table()

    def open_repeat_dialog(self):
        self.repeat_dialog = RepeatDialog(self)
        self.repeat_dialog.show()
        self.repeat_dialog.repeat_signal.connect(self.repeat_medicine)

    def repeat_medicine(self, repeat_values):
        if self.selected_row is not None:
            row = self.selected_row
            medicine_id = self.schedule_table.item(row, 0).data(
                Qt.ItemDataRole.UserRole
            )
            self.main_window.cursor.execute(
                "SELECT * FROM medicines WHERE id = ?", (medicine_id,)
            )
            medicine = self.main_window.cursor.fetchone()
            days = repeat_values["days"]
            hours = repeat_values["hours"]
            minutes = repeat_values["minutes"]
            date_obj = QDate.fromString(medicine[3], "yyyy-MM-dd")
            time_obj = QTime.fromString(medicine[4], "HH:mm")
            time_obj = time_obj.addSecs(minutes * 60 + hours * 3600)
            date_obj = date_obj.addDays(days)
            new_date = date_obj.toString("yyyy-MM-dd")
            new_time = time_obj.toString("HH:mm")
            self.main_window.cursor.execute(
                "INSERT INTO medicines (name, dosage, date, time) VALUES (?, ?, ?, ?)",
                (medicine[1], medicine[2], new_date, new_time),
            )
            self.main_window.conn.commit()
            self.update_table()

    def handle_selection_changed(self, selected, deselected):
        self.selected_row = selected.indexes()[
            0].row() if selected.indexes() else None
        self.repeat_button.setEnabled(self.selected_row is not None)
        self.delete_button.setEnabled(self.selected_row is not None)
        self.edit_button.setEnabled(self.selected_row is not None)

    def search_schedule(self, text):
        self.schedule_table.setRowCount(0)
        if text:
            self.main_window.cursor.execute(
                "SELECT * FROM medicines WHERE name LIKE ? OR dosage LIKE ? OR date LIKE ? OR time LIKE ? ORDER BY date ASC, time ASC",
                (f"%{text}%", f"%{text}%", f"%{text}%", f"%{text}%"),
            )
        else:
            self.main_window.cursor.execute(
                "SELECT * FROM medicines ORDER BY date ASC, time ASC"
            )
        medicines = self.main_window.cursor.fetchall()

        for i, medicine in enumerate(medicines):
            self.schedule_table.insertRow(i)
            self.schedule_table.setItem(i, 0, QTableWidgetItem(medicine[1]))
            self.schedule_table.setItem(i, 1, QTableWidgetItem(medicine[2]))
            self.schedule_table.setItem(i, 2, QTableWidgetItem(medicine[3]))
            self.schedule_table.setItem(i, 3, QTableWidgetItem(medicine[4]))
            self.schedule_table.item(i, 0).setData(Qt.ItemDataRole.UserRole,
                                                   medicine[0])


class EditMedicineDialog(QDialog):
    data_changed = pyqtSignal(dict)

    def __init__(self, medicine_data, main_window):
        super().__init__()
        self.setWindowTitle("Редактировать событие")
        self.setGeometry(100, 100, 300, 200)
        self.main_window = main_window

        self.medicine_history = self.main_window.get_medicine_history()

        medicine_label = QLabel("Лекарство:")
        self.medicine_combobox = QComboBox()
        self.medicine_combobox.addItems(self.medicine_history)
        self.medicine_combobox.setEditable(True)
        self.medicine_combobox.setCurrentText(medicine_data[1])

        dosage_label = QLabel("Дозировка:")
        self.dosage_edit = QLineEdit(medicine_data[2])

        date_label = QLabel("Дата:")
        self.date_edit = QDateEdit()
        self.date_edit.setDate(
            QDate.fromString(medicine_data[3], "yyyy-MM-dd"))

        time_label = QLabel("Время:")
        self.time_edit = QTimeEdit()
        self.time_edit.setTime(QTime.fromString(medicine_data[4], "HH:mm"))

        save_button = QPushButton("Сохранить")
        save_button.clicked.connect(self.save_changes)

        layout = QGridLayout()
        layout.addWidget(medicine_label, 0, 0)
        layout.addWidget(self.medicine_combobox, 0, 1)
        layout.addWidget(dosage_label, 1, 0)
        layout.addWidget(self.dosage_edit, 1, 1)
        layout.addWidget(date_label, 2, 0)
        layout.addWidget(self.date_edit, 2, 1)
        layout.addWidget(time_label, 3, 0)
        layout.addWidget(self.time_edit, 3, 1)
        layout.addWidget(save_button, 4, 0, 1, 2)

        self.setLayout(layout)

    def save_changes(self):

        medicine_name = self.medicine_combobox.currentText()
        dosage = self.dosage_edit.text()
        date = self.date_edit.date().toString("yyyy-MM-dd")
        time = self.time_edit.time().toString("HH:mm")
        if not medicine_name.strip():
            QMessageBox.warning(self, "Ошибка",
                                "Введите корректное название лекарства")
            return

        if not dosage.strip() or not dosage.isdigit() or int(dosage) <= 0:
            QMessageBox.warning(self, "Ошибка",
                                "Введите корректную дозировку лекарства")
            return

        current_datetime = datetime.datetime.now()
        selected_datetime = datetime.datetime.strptime(f"{date} {time}",
                                                       "%Y-%m-%d %H:%M")
        if selected_datetime < current_datetime:
            QMessageBox.warning(self, "Ошибка",
                                "Выберите корректную дату и время")
            return

        medicine_data = {
            "name": medicine_name,
            "dosage": dosage,
            "date": date,
            "time": time,
        }
        self.data_changed.emit(medicine_data)
        self.close()


class RepeatDialog(QDialog):
    repeat_signal = pyqtSignal(dict)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Повторить прием")
        self.setGeometry(100, 100, 200, 150)
        days_label = QLabel("Дней:")
        self.days_spinbox = QSpinBox()
        self.days_spinbox.setMinimum(0)
        self.days_spinbox.setMaximum(365)
        hours_label = QLabel("Часов:")
        self.hours_spinbox = QSpinBox()
        self.hours_spinbox.setMinimum(0)
        self.hours_spinbox.setMaximum(23)
        minutes_label = QLabel("Минут:")
        self.minutes_spinbox = QSpinBox()
        self.minutes_spinbox.setMinimum(0)
        self.minutes_spinbox.setMaximum(59)
        save_button = QPushButton("Сохранить")
        save_button.clicked.connect(self.save_repeat)
        layout = QGridLayout()
        layout.addWidget(days_label, 0, 0)
        layout.addWidget(self.days_spinbox, 0, 1)
        layout.addWidget(hours_label, 1, 0)
        layout.addWidget(self.hours_spinbox, 1, 1)
        layout.addWidget(minutes_label, 2, 0)
        layout.addWidget(self.minutes_spinbox, 2, 1)
        layout.addWidget(save_button, 3, 0, 1, 2)
        self.setLayout(layout)

    def save_repeat(self):
        days = self.days_spinbox.value()
        hours = self.hours_spinbox.value()
        minutes = self.minutes_spinbox.value()
        repeat_values = {"days": days, "hours": hours, "minutes": minutes}
        self.repeat_signal.emit(repeat_values)
        self.close()


class AddInventoryWindow(QWidget):
    def __init__(self, main_window):
        super().__init__()
        self.setWindowTitle("Добавить запас")
        self.setGeometry(100, 100, 300, 150)
        self.main_window = main_window
        self.medicine_history = self.main_window.get_medicine_history()
        medicine_label = QLabel("Лекарство:")
        self.medicine_combobox = QComboBox()
        self.medicine_combobox.addItems(sorted(
            self.medicine_history))
        self.medicine_combobox.setEditable(True)
        quantity_label = QLabel("Количество:")
        self.quantity_spinbox = QSpinBox()
        self.quantity_spinbox.setMinimum(1)
        save_button = QPushButton("Сохранить")
        save_button.clicked.connect(self.save_inventory)
        layout = QGridLayout()
        layout.addWidget(medicine_label, 0, 0)
        layout.addWidget(self.medicine_combobox, 0, 1)
        layout.addWidget(quantity_label, 1, 0)
        layout.addWidget(self.quantity_spinbox, 1, 1)
        layout.addWidget(save_button, 2, 0, 1, 2)
        self.setLayout(layout)

    def save_inventory(self):
        medicine_name = self.medicine_combobox.currentText()
        quantity = self.quantity_spinbox.value()
        if medicine_name:
            if quantity > 0:
                self.main_window.cursor.execute(
                    "INSERT INTO inventory (name, quantity) VALUES (?, ?)",
                    (medicine_name, quantity),
                )
                self.main_window.conn.commit()
                self.close()
            else:
                QMessageBox.warning(self, "Ошибка",
                                    "Количество таблеток должно быть больше 0")
        else:
            QMessageBox.warning(self, "Ошибка", "Введите название лекарства")


class InventoryWindow(QWidget):
    def __init__(self, main_window):
        super().__init__()
        self.setWindowTitle("Запасы лекарств")
        self.setGeometry(100, 100, 400, 300)
        self.main_window = main_window
        self.selected_row = None

        self.inventory_table = QTableWidget()
        self.inventory_table.setColumnCount(2)
        self.inventory_table.setHorizontalHeaderLabels(
            ["Лекарство", "Количество"])
        self.inventory_table.setSelectionBehavior(
            QTableWidget.SelectionBehavior.SelectRows)
        self.inventory_table.setSelectionMode(
            QTableWidget.SelectionMode.SingleSelection)

        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText("Поиск...")
        self.search_edit.textChanged.connect(self.search_inventory)

        self.delete_button = QPushButton("Удалить")
        self.delete_button.clicked.connect(self.delete_inventory_item)
        self.edit_button = QPushButton("Изменить")
        self.edit_button.clicked.connect(self.edit_inventory_item)
        self.add_to_log_button = QPushButton("Добавить в журнал")
        self.add_to_log_button.clicked.connect(self.add_to_log)

        layout = QVBoxLayout()
        layout.addWidget(self.search_edit)
        layout.addWidget(self.inventory_table)
        button_layout = QHBoxLayout()
        button_layout.addWidget(self.delete_button)
        button_layout.addWidget(self.edit_button)
        button_layout.addWidget(self.add_to_log_button)
        layout.addLayout(button_layout)
        self.setLayout(layout)

        self.inventory_table.selectionModel().selectionChanged.connect(
            self.handle_selection_changed
        )

        self.update_table()

    def update_table(self):
        self.inventory_table.setRowCount(0)
        self.main_window.cursor.execute(
            "SELECT * FROM inventory ORDER BY name ASC"
        )
        inventory_items = self.main_window.cursor.fetchall()
        for i, item in enumerate(inventory_items):
            self.inventory_table.insertRow(i)
            self.inventory_table.setItem(i, 0, QTableWidgetItem(item[1]))
            self.inventory_table.setItem(i, 1, QTableWidgetItem(str(item[2])))
            self.inventory_table.item(i, 0).setData(
                Qt.ItemDataRole.UserRole, item[0]
            )

    def delete_inventory_item(self):
        selected_rows = self.inventory_table.selectionModel().selectedRows()
        if selected_rows:
            row = selected_rows[0].row()
            if QMessageBox.question(
                    self,
                    "Удаление",
                    "Вы уверены, что хотите удалить этот элемент?",
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                    QMessageBox.StandardButton.No,
            ) == QMessageBox.StandardButton.Yes:
                inventory_id = self.inventory_table.item(row, 0).data(
                    Qt.ItemDataRole.UserRole
                )
                self.main_window.cursor.execute(
                    "DELETE FROM inventory WHERE id = ?", (inventory_id,)
                )
                self.main_window.conn.commit()
                self.update_table()

    def edit_inventory_item(self):
        selected_rows = self.inventory_table.selectionModel().selectedRows()
        if selected_rows:
            row = selected_rows[0].row()
            inventory_id = self.inventory_table.item(row, 0).data(
                Qt.ItemDataRole.UserRole
            )
            self.main_window.cursor.execute(
                "SELECT * FROM inventory WHERE id = ?", (inventory_id,)
            )
            inventory_item = self.main_window.cursor.fetchone()
            self.edit_dialog = EditInventoryDialog(
                inventory_item, self.main_window
            )
            self.edit_dialog.setWindowTitle("Редактировать элемент")

            self.edit_dialog.data_changed.connect(self.update_data)

            self.edit_dialog.show()

    def update_data(self, inventory_data):
        selected_rows = self.inventory_table.selectionModel().selectedRows()
        if selected_rows:
            row = selected_rows[0].row()
            inventory_id = self.inventory_table.item(row, 0).data(
                Qt.ItemDataRole.UserRole
            )
            self.main_window.cursor.execute(
                "UPDATE inventory SET name = ?, quantity = ? WHERE id = ?",
                (
                    inventory_data["name"],
                    inventory_data["quantity"], inventory_id,
                ),
            )
            self.main_window.conn.commit()
            self.update_table()

    def add_to_log(self):
        selected_rows = self.inventory_table.selectionModel().selectedRows()
        if selected_rows:
            row = selected_rows[0].row()
            medicine_name = self.inventory_table.item(row, 0).text()
            self.main_window.cursor.execute(
                "INSERT INTO medicines_log (name) VALUES (?)",
                (medicine_name,)
            )
            self.main_window.conn.commit()
            QMessageBox.information(
                self, "Успешно",
                f"Лекарство '{medicine_name}' добавлено в журнал"
            )

    def search_inventory(self, text):
        self.inventory_table.setRowCount(0)
        if text:
            self.main_window.cursor.execute(
                "SELECT * FROM inventory WHERE name LIKE ? ORDER BY name ASC",
                (f"%{text}%",)
            )
        else:
            self.main_window.cursor.execute(
                "SELECT * FROM inventory ORDER BY name ASC"
            )
        inventory_items = self.main_window.cursor.fetchall()
        for i, item in enumerate(inventory_items):
            self.inventory_table.insertRow(i)
            self.inventory_table.setItem(i, 0, QTableWidgetItem(item[1]))
            self.inventory_table.setItem(i, 1, QTableWidgetItem(str(item[2])))
            self.inventory_table.item(i, 0).setData(
                Qt.ItemDataRole.UserRole, item[0]
            )

    def handle_selection_changed(self, selected, deselected):
        self.selected_row = selected.indexes()[
            0].row() if selected.indexes() else None
        self.delete_button.setEnabled(self.selected_row is not None)
        self.edit_button.setEnabled(self.selected_row is not None)
        self.add_to_log_button.setEnabled(self.selected_row is not None)


class EditInventoryDialog(QDialog):
    data_changed = pyqtSignal(dict)

    def __init__(self, inventory_item, main_window):
        super().__init__()
        self.setWindowTitle("Редактировать элемент")
        self.setGeometry(100, 100, 300, 150)
        self.main_window = main_window

        self.medicine_history = self.main_window.get_medicine_history()

        medicine_label = QLabel("Лекарство:")
        self.medicine_combobox = QComboBox()
        self.medicine_combobox.addItems(self.medicine_history)
        self.medicine_combobox.setEditable(True)
        self.medicine_combobox.setCurrentText(inventory_item[1])

        quantity_label = QLabel("Количество:")
        self.quantity_spinbox = QSpinBox()
        self.quantity_spinbox.setMinimum(0)
        self.quantity_spinbox.setValue(inventory_item[2])

        save_button = QPushButton("Сохранить")
        save_button.clicked.connect(self.save_changes)

        layout = QGridLayout()
        layout.addWidget(medicine_label, 0, 0)
        layout.addWidget(self.medicine_combobox, 0, 1)
        layout.addWidget(quantity_label, 1, 0)
        layout.addWidget(self.quantity_spinbox, 1, 1)
        layout.addWidget(save_button, 2, 0, 1, 2)

        self.setLayout(layout)

    def save_changes(self):
        medicine_name = self.medicine_combobox.currentText()
        quantity = self.quantity_spinbox.value()

        if not medicine_name.strip():
            QMessageBox.warning(self, "Ошибка",
                                "Введите корректное название лекарства")
            return
        if quantity <= 0:
            QMessageBox.warning(self, "Ошибка",
                                "Введите корректное количество таблеток")
            return

        inventory_data = {
            "name": medicine_name,
            "quantity": quantity,
        }
        self.data_changed.emit(inventory_data)
        self.close()


class HelpWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Помощь")
        self.setGeometry(100, 100, 400, 300)

        help_text = """

      Добавить лекарство:
      Введите название лекарства.
      Введите дозировку лекарства.
      Укажите дату начала приема.
      Укажите время начала приема.
      Нажмите "Сохранить".

      График приема:
      Отображает список запланированных приемов лекарств.
      Вы можете удалить, изменить или повторить прием лекарства, выбрав его в таблице.

      Запасы лекарств:
      Отображает список имеющихся лекарств и их количество.
      Вы можете добавить новый запас лекарства.
      Вы можете удалить выбранный запас.
      Вы можете изменить название лекарства и количество таблеток в выбранном запасе.

      Добавить запас:
      Введите название лекарства.
      Введите количество таблеток.
      Нажмите "Сохранить".

      Сброс данных:
      Нажмите D на клавиатуре, чтобы сбросить все данные.

      Примечания:
      Приложение хранит историю названий лекарств, которые вы использовали ранее. 
    """

        help_label = QLabel(help_text)
        help_label.setWordWrap(True)

        scroll_area = QScrollArea()
        scroll_area.setWidget(help_label)
        scroll_area.setWidgetResizable(True)

        layout = QVBoxLayout()
        layout.addWidget(scroll_area)
        self.setLayout(layout)


class NotificationTimer:
    def __init__(self, main_window):
        self.main_window = main_window
        self.timer = QTimer()
        self.timer.timeout.connect(self.check_notifications)

        self.main_window.cursor.execute('''
        CREATE TABLE IF NOT EXISTS medicines_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            dosage TEXT,
            date TEXT,
            time TEXT,
            received_time TEXT
        )
        ''')
        self.main_window.conn.commit()

    def check_notifications(self):
        now = datetime.datetime.now()
        self.main_window.cursor.execute(
            "SELECT id, name, dosage, date, time FROM medicines WHERE date <= ? AND time <= ? ORDER BY date ASC, time ASC",
            (now.strftime("%Y-%m-%d"), now.strftime("%H:%M")),
        )
        medicines = self.main_window.cursor.fetchall()

        for medicine in medicines:
            medicine_date = datetime.datetime.strptime(
                medicine[3] + " " + medicine[4], "%Y-%m-%d %H:%M")
            if medicine_date <= now:
                notification.notify(
                    title=f"Время приема лекарства",
                    message=f"{medicine[1]} ({medicine[2]})",
                    timeout=10,
                )
                self.main_window.cursor.execute(
                    "INSERT INTO medicines_log (name, dosage, date, time, received_time) VALUES (?, ?, ?, ?, ?)",
                    (medicine[1], medicine[2], medicine[3], medicine[4],
                     datetime.datetime.now().strftime("%Y-%m-%d %H:%M"))
                )
                self.main_window.cursor.execute(
                    "DELETE FROM medicines WHERE id = ?", (medicine[0],))
                self.main_window.conn.commit()


class LogWindow(QWidget):
    def __init__(self, main_window):
        super().__init__()
        self.setWindowTitle("Журнал приема")
        self.setGeometry(100, 100, 400, 300)
        self.main_window = main_window
        self.selected_row = None

        self.log_table = QTableWidget()
        self.log_table.setColumnCount(3)
        self.log_table.setHorizontalHeaderLabels(
            ["Лекарство", "Дата", "Описание"])
        self.log_table.setSelectionBehavior(
            QTableWidget.SelectionBehavior.SelectRows)
        self.log_table.setSelectionMode(
            QTableWidget.SelectionMode.SingleSelection)

        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText("Поиск...")
        self.search_edit.textChanged.connect(self.search_log)

        self.add_or_edit_button = QPushButton("Добавить/Изменить описание")
        self.add_or_edit_button.clicked.connect(self.add_or_edit_description)
        self.add_or_edit_button.setEnabled(
            False)

        layout = QVBoxLayout()
        layout.addWidget(self.search_edit)
        layout.addWidget(self.log_table)
        layout.addWidget(self.add_or_edit_button)
        self.setLayout(layout)

        self.update_table()

        self.log_table.selectionModel().selectionChanged.connect(
            self.handle_selection_changed
        )

    def update_table(self):
        self.log_table.setRowCount(0)
        self.main_window.cursor.execute(
            "SELECT * FROM medicines_log ORDER BY date ASC, time ASC")
        medicine_data = self.main_window.cursor.fetchall()
        for i, item in enumerate(medicine_data):
            self.log_table.insertRow(i)
            self.log_table.setItem(i, 0, QTableWidgetItem(
                item[1]))
            self.log_table.setItem(i, 1, QTableWidgetItem(item[3]))
            self.log_table.setItem(i, 2, QTableWidgetItem(item[6]))

            self.log_table.item(i, 0).setData(Qt.ItemDataRole.UserRole,
                                              item[0])

    def add_or_edit_description(self):
        if self.selected_row is not None:
            description, ok = QInputDialog.getText(
                self, "Описание", "Введите описание приема:",
                QLineEdit.EchoMode.Normal
            )
            if ok:
                medicine_id = self.log_table.item(
                    self.selected_row, 0
                ).data(Qt.ItemDataRole.UserRole)
                self.main_window.cursor.execute(
                    "UPDATE medicines_log SET description = ? WHERE id = ?",
                    (description, medicine_id),
                )
                self.main_window.conn.commit()
                QMessageBox.information(
                    self, "Успешно", f"Описание добавлено/изменено в журнале"
                )
                self.update_table()

    def search_log(self, text):
        self.log_table.setRowCount(0)
        if text:
            self.main_window.cursor.execute(
                "SELECT * FROM medicines_log WHERE name LIKE ? ORDER BY date ASC, time ASC",
                (f"%{text}%",)
            )
        else:
            self.main_window.cursor.execute(
                "SELECT * FROM medicines_log ORDER BY date ASC, time ASC"
            )
        inventory_items = self.main_window.cursor.fetchall()
        for i, item in enumerate(inventory_items):
            self.log_table.insertRow(i)
            self.log_table.setItem(i, 0, QTableWidgetItem(item[1]))
            self.log_table.setItem(i, 1, QTableWidgetItem(item[3]))
            self.log_table.setItem(i, 2, QTableWidgetItem(item[5]))
            self.log_table.item(i, 0).setData(
                Qt.ItemDataRole.UserRole, item[0]
            )

    def handle_selection_changed(self, selected, deselected):
        if selected.indexes():
            self.selected_row = selected.indexes()[0].row()
            self.add_or_edit_button.setEnabled(True)
        else:
            self.selected_row = None
            self.add_or_edit_button.setEnabled(False)





if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    notification_timer = NotificationTimer(
        window)
    window.show()
    sys.exit(app.exec())
