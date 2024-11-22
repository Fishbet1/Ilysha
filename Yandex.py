import datetime
import sqlite3
import sys

from PyQt6.QtCore import Qt, pyqtSignal, QDate, QTime, QEvent, QTimer, QSize
from PyQt6.QtGui import QFont, QIcon, QPixmap
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
    QTableWidget,
    QTableWidgetItem,
    QDialog,
    QSpinBox,
    QScrollArea,
    QInputDialog, QSizePolicy,
)
from plyer import notification


class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Приложение для лекарств")
        self.setWindowIcon(
            QIcon('images/icon.ico'))
        self.setStyleSheet(
            "background-image: url('images/main.jpg');")
        self.setGeometry(100, 100, 500, 350)

        self.conn = sqlite3.connect("medicines.db")
        self.cursor = self.conn.cursor()

        self.cursor.execute('''
              CREATE TABLE IF NOT EXISTS medicines (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT,
                dosage INTEGER,
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
                dosage INTEGER,
                date TEXT,
                time TEXT,
                received_time TEXT,
                description TEXT
              )
            ''')
        self.conn.commit()
        self.add_inventory_button = QPushButton("Добавить запас")
        self.add_inventory_button.clicked.connect(
            self.open_add_inventory_window)

        self.view_inventory_button = QPushButton("Запасы лекарств")
        self.view_inventory_button.clicked.connect(self.open_inventory_window)

        self.add_medicine_button = QPushButton("Добавить прием")
        self.add_medicine_button.clicked.connect(self.open_add_medicine_window)

        self.view_schedule_button = QPushButton("График приема")
        self.view_schedule_button.clicked.connect(self.open_schedule_window)

        self.view_log_button = QPushButton("Журнал приема")
        self.view_log_button.clicked.connect(self.open_log_window)

        self.help_button = QPushButton("Помощь")
        self.help_button.clicked.connect(self.open_help_window)

        welcome_label = QLabel(
            "Добро пожаловать в приложение для управления лекарствами")
        font = QFont()
        font.setPointSize(16)
        font.setBold(True)
        welcome_label.setFont(font)
        welcome_label.setAlignment(
            Qt.AlignmentFlag.AlignCenter)

        grid_layout = QGridLayout()
        grid_layout.addWidget(self.add_inventory_button, 0, 0)
        grid_layout.addWidget(self.view_inventory_button, 1, 0)
        grid_layout.addWidget(self.add_medicine_button, 0, 1)
        grid_layout.addWidget(self.view_schedule_button, 1, 1)

        button_layout = QVBoxLayout()
        button_layout.addWidget(self.view_log_button)
        button_layout.addWidget(self.help_button)

        main_layout = QVBoxLayout()
        main_layout.addWidget(welcome_label)
        main_layout.addLayout(grid_layout)
        main_layout.addLayout(button_layout)
        self.setLayout(main_layout)

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
            "SELECT DISTINCT name FROM medicines UNION SELECT DISTINCT name FROM medicines_log"
        )
        medicine_names = [row[0] for row in self.cursor.fetchall()]
        return sorted(medicine_names)

    def reset_data(self):
        if QMessageBox.question(
                self,
                "Сброс данных",
                "Вы уверены, что хотите сбросить все данные?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No,
        ) == QMessageBox.StandardButton.Yes:
            try:
                self.cursor.execute("DELETE FROM medicines")
                self.cursor.execute("DELETE FROM inventory")
                self.cursor.execute("DELETE FROM medicines_log")
                self.conn.commit()
                QMessageBox.information(self, "Сброс данных",
                                        "Все данные успешно сброшены")
            except sqlite3.Error as e:
                QMessageBox.critical(self, "Ошибка",
                                     f"Ошибка при сбросе данных: {e}")
            except Exception as e:
                QMessageBox.critical(self, "Ошибка",
                                     f"Непредвиденная ошибка: {e}")

    def eventFilter(self, watched: 'QObject', event: 'QEvent') -> bool:
        if event.type() == QEvent.Type.KeyPress and event.key() == Qt.Key.Key_D:
            self.reset_data()
        return super().eventFilter(watched, event)


class AddMedicineWindow(QDialog):
    def __init__(self, main_window):
        super().__init__()
        self.setWindowTitle("Добавить прием")
        self.setWindowIcon(
            QIcon('images/icon.ico'))
        self.setStyleSheet(
            "background-image: url('images/addmed.jpg');")
        self.main_window = main_window
        self.medicine_list = self.get_medicine_list()

        medicine_label = QLabel("Лекарство:")
        self.medicine_combobox = QComboBox()
        self.medicine_combobox.addItems(sorted(self.medicine_list))
        self.medicine_combobox.setEditable(True)

        dosage_label = QLabel("Дозировка:")
        self.dosage_spinbox = QSpinBox()
        self.dosage_spinbox.setMinimum(1)

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
        layout.addWidget(self.dosage_spinbox, 1, 1)
        layout.addWidget(date_label, 2, 0)
        layout.addWidget(self.date_edit, 2, 1)
        layout.addWidget(time_label, 3, 0)
        layout.addWidget(self.time_edit, 3, 1)
        layout.addWidget(save_button, 4, 0, 1, 2)
        self.setLayout(layout)

    def save_medicine(self):
        medicine_name = self.medicine_combobox.currentText()
        dosage = self.dosage_spinbox.value()
        date = self.date_edit.date().toString("yyyy-MM-dd")
        time = self.time_edit.time().toString("HH:mm")

        if not medicine_name:
            QMessageBox.warning(self, "Ошибка", "Введите название лекарства!")
            return

        inventory_level = self.check_inventory(medicine_name)
        if inventory_level is None:
            QMessageBox.warning(self, "Ошибка",
                                f"Лекарство '{medicine_name}' отсутствует на складе. Добавьте его в запасы.")
            return
        elif dosage > inventory_level:
            QMessageBox.warning(self, "Ошибка",
                                f"Недостаточно лекарства '{medicine_name}' на складе. Требуется {dosage}, а есть {inventory_level}.")
            return

        current_datetime = datetime.datetime.now()
        entered_datetime = datetime.datetime.strptime(date + " " + time,
                                                      "%Y-%m-%d %H:%M")

        if entered_datetime >= current_datetime:
            try:
                self.main_window.conn.execute("BEGIN TRANSACTION")
                self.main_window.cursor.execute(
                    "INSERT INTO medicines (name, dosage, date, time) VALUES (?, ?, ?, ?)",
                    (medicine_name, dosage, date, time)
                )
                self.update_inventory(medicine_name, dosage)
                self.main_window.conn.commit()
                self.check_and_notify_zero_inventory(medicine_name)
                self.close()
            except sqlite3.IntegrityError as e:
                self.main_window.conn.rollback()
                QMessageBox.critical(self, "Ошибка",
                                     f"Ошибка добавления приема: {e}")
            except sqlite3.Error as e:
                self.main_window.conn.rollback()
                QMessageBox.critical(self, "Ошибка",
                                     f"Ошибка базы данных: {e}")
            except Exception as e:
                self.main_window.conn.rollback()
                QMessageBox.critical(self, "Ошибка",
                                     f"Произошла неизвестная ошибка: {e}")
                import traceback
                traceback.print_exc()
        else:
            QMessageBox.warning(self, "Ошибка",
                                "Время приема не может быть раньше текущего времени")

    def update_inventory(self, medicine_name, quantity):
        try:
            self.main_window.cursor.execute(
                "UPDATE inventory SET quantity = quantity - ? WHERE name = ?", (quantity, medicine_name)
            )
        except sqlite3.Error as e:
            QMessageBox.critical(self, "Ошибка", f"Ошибка обновления запасов: {e}")

    def check_and_notify_zero_inventory(self, medicine_name):
        try:
            self.main_window.cursor.execute("SELECT quantity FROM inventory WHERE name = ?", (medicine_name,))
            result = self.main_window.cursor.fetchone()
            if result and result[0] <= 0:
                notification.notify(
                    title=f"Уведомление",
                    message=f"Лекарство '{medicine_name}' закончилось.",
                    app_name="MyMedicineApp",
                    timeout=10,
                    app_icon="images/icon.ico",
                )
        except (sqlite3.Error, IndexError) as e:
            QMessageBox.critical(self, "Ошибка", f"Ошибка проверки запасов: {e}")

    def get_medicine_list(self):
        medicine_list = set()
        medicine_list.update(
            self.main_window.get_medicine_history())
        medicine_list.update(
            self.get_medicines_from_inventory())
        return list(medicine_list)

    def get_medicines_from_inventory(self):
        self.main_window.cursor.execute("SELECT name FROM inventory")
        result = self.main_window.cursor.fetchall()
        return [item[0] for item in result]

    def check_inventory(self, medicine_name):
        self.main_window.cursor.execute(
            "SELECT quantity FROM inventory WHERE name = ?", (medicine_name,))
        result = self.main_window.cursor.fetchone()
        return result[0] if result else None


class ScheduleWindow(QWidget):
    def __init__(self, main_window):
        super().__init__()
        self.setWindowTitle("График приема")
        self.setWindowIcon(
            QIcon('images/icon.ico'))
        self.setStyleSheet(
            "background-image: url('images/shedule.jpg');")
        self.setGeometry(100, 100, 450, 300)
        self.main_window = main_window
        self.selected_row = None

        self.cancel_button = QPushButton("Отменить прием")
        self.cancel_button.clicked.connect(self.cancel_medicine)
        self.cancel_button.setEnabled(False)



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


        layout = QVBoxLayout()
        layout.addWidget(self.search_edit)
        layout.addWidget(self.schedule_table)
        layout.addWidget(self.cancel_button)

        self.setLayout(layout)

        self.schedule_table.selectionModel().selectionChanged.connect(
            self.handle_selection_changed)

        self.update_table()

    def update_table(self):
        self.schedule_table.setRowCount(0)
        self.main_window.cursor.execute(
            "SELECT id, name, dosage, date, time FROM medicines ORDER BY date ASC, time ASC"
        )
        medicines = self.main_window.cursor.fetchall()

        for i, medicine in enumerate(medicines):
            self.schedule_table.insertRow(i)
            self.schedule_table.setItem(i, 0, QTableWidgetItem(str(medicine[1])))
            self.schedule_table.setItem(i, 1, QTableWidgetItem(str(medicine[2])))
            self.schedule_table.setItem(i, 2, QTableWidgetItem(str(medicine[3])))
            self.schedule_table.setItem(i, 3, QTableWidgetItem(str(medicine[4])))
            self.schedule_table.item(i, 0).setData(Qt.ItemDataRole.UserRole,
                                                   medicine[0])



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



    def handle_selection_changed(self, selected, deselected):
        if self.schedule_table.selectedItems():
            self.cancel_button.setEnabled(True)
        else:
            self.cancel_button.setEnabled(False)

    def cancel_medicine(self):
        selected_rows = self.schedule_table.selectedIndexes()
        if selected_rows:
            row = selected_rows[0].row()
            medicine_id = self.schedule_table.item(row, 0).data(
                Qt.ItemDataRole.UserRole)
            medicine_name = self.schedule_table.item(row,
                                                     0).text()
            try:
                dosage = int(self.schedule_table.item(row,
                                                      1).text())
            except ValueError:
                QMessageBox.critical(self, "Ошибка",
                                     "Неверный формат дозировки. Дозировка должна быть целым числом.")
                return

            if QMessageBox.question(
                    self,
                    "Отмена приема",
                    "Вы уверены, что хотите отменить этот прием?",
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                    QMessageBox.StandardButton.No,
            ) == QMessageBox.StandardButton.Yes:
                try:
                    self.return_to_inventory(medicine_name, dosage)
                    self.main_window.cursor.execute(
                        "DELETE FROM medicines WHERE id = ?", (medicine_id,))
                    self.main_window.conn.commit()
                    self.update_table()
                except sqlite3.Error as e:
                    QMessageBox.critical(self, "Ошибка",
                                         f"Ошибка отмены приема или обновления запасов: {e}")
                except Exception as e:
                    QMessageBox.critical(self, "Ошибка",
                                         f"Неизвестная ошибка: {e}")

    def return_to_inventory(self, medicine_name, quantity):
        try:
            self.main_window.cursor.execute(
                "UPDATE inventory SET quantity = quantity + ? WHERE name = ?",
                (quantity, medicine_name)
            )
            self.main_window.conn.commit()
        except sqlite3.Error as e:
            QMessageBox.critical(self, "Ошибка",
                                 f"Ошибка возврата лекарства в запас: {e}")

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
        self.setWindowIcon(
            QIcon('images/icon.ico'))
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
        self.setWindowIcon(
            QIcon('images/icon.ico'))
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
        self.setWindowIcon(
            QIcon('images/icon.ico'))
        self.setWindowTitle("Добавить запас")
        self.setStyleSheet(
            "background-image: url('images/addinv.jpg');")
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

        if not medicine_name:
            QMessageBox.warning(self, "Ошибка", "Введите название лекарства!")
            return

        try:
            self.main_window.cursor.execute(
                "SELECT quantity FROM inventory WHERE name = ?",
                (medicine_name,))
            existing_quantity = self.main_window.cursor.fetchone()

            if existing_quantity:
                QMessageBox.information(
                    self,
                    "Лекарство уже существует",
                    f"Лекарство '{medicine_name}' уже существует в запасах. Пополните запас в окне запасов."
                )
                return

            else:
                self.main_window.cursor.execute(
                    "INSERT INTO inventory (name, quantity) VALUES (?, ?)",
                    (medicine_name, quantity))
                self.main_window.conn.commit()
                self.close()

        except sqlite3.IntegrityError as e:
            QMessageBox.critical(self, "Ошибка",
                                 f"Лекарство с таким названием уже существует: {e}")
        except sqlite3.Error as e:
            QMessageBox.critical(self, "Ошибка", f"Ошибка базы данных: {e}")
        except Exception as e:
            QMessageBox.critical(self, "Ошибка",
                                 f"Произошла неизвестная ошибка: {e}")
            import traceback
            traceback.print_exc()

class InventoryWindow(QWidget):
    def __init__(self, main_window):
        super().__init__()
        self.setWindowTitle("Запасы лекарств")
        self.setWindowIcon(
            QIcon('images/icon.ico'))
        self.setStyleSheet(
            "background-image: url('images/invent.jpg');")
        self.setGeometry(100, 100, 400, 300)
        self.main_window = main_window
        self.selected_row = None
        self.inventory_table = QTableWidget()
        self.inventory_table.setColumnCount(2)
        self.inventory_table.setHorizontalHeaderLabels(
            ["Лекарство", "Количество"])
        self.inventory_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.inventory_table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText("Поиск...")
        self.search_edit.textChanged.connect(self.search_inventory)
        self.delete_button = QPushButton("Удалить")
        self.delete_button.clicked.connect(self.delete_inventory_item)
        self.delete_button.setEnabled(False)
        self.edit_button = QPushButton("Изменить")
        self.edit_button.clicked.connect(self.edit_inventory_item)
        self.edit_button.setEnabled(False)

        layout = QVBoxLayout()
        layout.addWidget(self.search_edit)
        layout.addWidget(self.inventory_table)
        button_layout = QHBoxLayout()
        button_layout.addWidget(self.delete_button)
        button_layout.addWidget(self.edit_button)
        layout.addLayout(button_layout)
        self.setLayout(layout)
        self.inventory_table.selectionModel().selectionChanged.connect(
            self.handle_selection_changed
        )
        self.update_table()

    def update_table(self):
        self.inventory_table.setRowCount(0)
        try:
            self.main_window.cursor.execute("SELECT * FROM inventory")
            inventory_data = self.main_window.cursor.fetchall()
            for i, item in enumerate(inventory_data):
                self.inventory_table.insertRow(i)
                name_item = QTableWidgetItem(item[1])
                name_item.setData(Qt.ItemDataRole.UserRole,
                                  item[0])
                self.inventory_table.setItem(i, 0, name_item)
                self.inventory_table.setItem(i, 1,
                                             QTableWidgetItem(str(item[2])))

        except sqlite3.Error as e:
            QMessageBox.critical(self, "Ошибка",
                                 f"Ошибка при загрузке данных: {e}")
        except Exception as e:
            QMessageBox.critical(self, "Ошибка",
                                 f"Произошла неизвестная ошибка: {e}")

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


class EditInventoryDialog(QDialog):
    data_changed = pyqtSignal(dict)

    def __init__(self, inventory_item, main_window):
        super().__init__()
        self.setWindowIcon(
            QIcon('images/icon.ico'))
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
        self.setWindowTitle("Справка")
        self.setWindowIcon(
            QIcon('images/icon.ico'))
        self.setFont(QFont("Arial", 11))
        self.create_ui()
        self.setFixedSize(800, 650)

    def create_ui(self):
        title_label = QLabel(
            "<h1>Добро пожаловать!</h1>")
        title_label.setStyleSheet(
            "font-size: 17px;")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)


        introduction = QLabel(
            """Это приложение поможет вам отслеживать приём лекарств и контролировать наличие запасов.
             Перед использованием приложения необходимо добавить лекарства в запасы."""
        )
        introduction.setWordWrap(True)
        introduction.setAlignment(Qt.AlignmentFlag.AlignLeft)

        sections = [
            ("Добавление лекарств в запасы", """1. Откройте окно «Запасы».
2. Введите название лекарства в поле «Название лекарства».
3. Укажите количество в поле «Количество».
4. Нажмите кнопку «Сохранить»."""),
            ("Добавление приема лекарств", """1. Откройте окно «Добавить прием».
2. Выберите лекарство из выпадающего списка. Список содержит лекарства, добавленные в «Запасах».
3. Укажите дозировку.
4. Выберите дату и время приема.
5. Нажмите кнопку «Сохранить». Приложение проверит наличие достаточного количества лекарства. При недостатке лекарства появится предупреждение.
После добавления, количество лекарства уменьшится.  Если лекарство закончилось, появится сообщение об этом."""),
            ("Просмотр расписания", """В этом окне отображается список запланированных приемов лекарств, отсортированных по дате и времени."""),
            ("Функция сброса данных", """Нажатие клавиши «D» на клавиатуре (в любом окне приложения) приведёт к удалению всех данных из приложения.  Данная операция необратима!""")
        ]

        main_layout = QVBoxLayout()
        main_layout.addWidget(title_label)
        main_layout.addWidget(introduction)


        for title, content in sections:
            section_title = QLabel(f"<h2>{title}</h2>")
            section_title.setAlignment(Qt.AlignmentFlag.AlignLeft)
            section_content = QLabel(content)
            section_content.setWordWrap(True)
            section_content.setAlignment(Qt.AlignmentFlag.AlignLeft)
            main_layout.addWidget(section_title)
            main_layout.addWidget(section_content)

        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setWidget(QWidget())
        scroll_area.widget().setLayout(main_layout)
        scroll_area.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

        final_layout = QVBoxLayout()
        final_layout.addWidget(scroll_area)
        self.setLayout(final_layout)
        self.image_label = QLabel()
        self.image_label.setAlignment(
            Qt.AlignmentFlag.AlignCenter)
        self.image_label.setFixedSize(QSize(700, 350))
        self.set_image(
            "images/good_day.jpg")

        main_layout.addWidget(
            self.image_label)

    def set_image(self, image_path):
        try:
            pixmap = QPixmap(image_path)
            pixmap = pixmap.scaled(self.image_label.size(),
                                   Qt.AspectRatioMode.KeepAspectRatio,
                                   Qt.TransformationMode.SmoothTransformation)
            self.image_label.setPixmap(pixmap)
        except Exception as e:
            QMessageBox.warning(self, "Ошибка",
                                f"Не удалось загрузить изображение: {e}")


class NotificationTimer:
    def __init__(self, main_window):
        self.main_window = main_window
        self.timer = QTimer()
        self.timer.timeout.connect(self.check_notifications)
        self.timer.start(6000)

        self.main_window.cursor.execute('''
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
                    app_name="MyMedicineApp",
                    timeout=10,
                    app_icon="images/icon.ico",
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
        self.setWindowIcon(
            QIcon('images/icon.ico'))
        self.setWindowTitle("Журнал приема")
        self.setStyleSheet(
            "background-image: url('images/log.jpg');")
        self.setGeometry(100, 100, 550, 400)
        self.main_window = main_window
        self.selected_row = None

        self.log_table = QTableWidget()
        self.log_table.setColumnCount(5)
        self.log_table.setHorizontalHeaderLabels(
            ["Лекарство", "Дозировка", "Дата", "Время", "Описание"])
        self.log_table.setSelectionBehavior(
            QTableWidget.SelectionBehavior.SelectRows)
        self.log_table.setSelectionMode(
            QTableWidget.SelectionMode.SingleSelection)

        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText("Поиск...")
        self.search_edit.textChanged.connect(self.search_log)

        self.add_or_edit_button = QPushButton("Добавить/Изменить событие")
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
            "SELECT id, name, dosage, date, time, description FROM medicines_log ORDER BY date DESC, time DESC"
        )
        medicine_data = self.main_window.cursor.fetchall()
        for i, item in enumerate(medicine_data):
            self.log_table.insertRow(i)
            self.log_table.setItem(i, 0,
                                   QTableWidgetItem(item[1]))
            self.log_table.setItem(i, 1,
                                   QTableWidgetItem(str(item[2])))
            self.log_table.setItem(i, 2, QTableWidgetItem(item[3]))
            self.log_table.setItem(i, 3, QTableWidgetItem(item[4]))
            self.log_table.setItem(i, 4, QTableWidgetItem(item[5]))
            self.log_table.item(i, 0).setData(Qt.ItemDataRole.UserRole,
                                              item[0])

    def add_or_edit_description(self):
        if self.selected_row is not None:
            description, ok = QInputDialog.getText(
                self, "Описание", "Введите описание приема:",
                QLineEdit.EchoMode.Normal
            )
            if ok:
                try:
                    row = self.selected_row
                    medicine_id = self.log_table.item(row, 0).data(
                        Qt.ItemDataRole.UserRole)
                    if medicine_id is None:
                        QMessageBox.critical(self, "Ошибка",
                                             "Не удалось получить ID записи.")
                        return

                    self.main_window.cursor.execute(
                        "UPDATE medicines_log SET description = ? WHERE id = ?",
                        (description, medicine_id)
                    )
                    self.main_window.conn.commit()
                    QMessageBox.information(self, "Успешно",
                                            f"Описание добавлено/изменено в журнале")
                    self.update_table()

                except sqlite3.Error as e:
                    self.main_window.conn.rollback()
                    QMessageBox.critical(self, "Ошибка БД",
                                         f"Ошибка при работе с базой данных: {e}")
                except Exception as e:
                    QMessageBox.critical(self, "Ошибка",
                                         f"Произошла неизвестная ошибка: {e}")
                    import traceback
                    traceback.print_exc()

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
            self.log_table.setItem(i, 0, QTableWidgetItem(str(item[1])))
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
