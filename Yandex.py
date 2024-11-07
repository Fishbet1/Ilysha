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
)
from PyQt6.QtCore import Qt, pyqtSignal, QDate, QTime


class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Лекарства")
        self.setGeometry(100, 100, 400, 300)
        welcome_label = QLabel(
            "Добро пожаловать в приложение для управления лекарствами")
        add_medicine_button = QPushButton("Добавить лекарство")
        add_medicine_button.clicked.connect(self.open_add_medicine_window)
        schedule_button = QPushButton("График приема")
        schedule_button.clicked.connect(self.open_schedule_window)
        inventory_button = QPushButton("Запасы лекарств")
        inventory_button.clicked.connect(self.open_inventory_window)
        layout = QVBoxLayout()
        layout.addWidget(welcome_label)
        layout.addWidget(add_medicine_button)
        layout.addWidget(schedule_button)
        layout.addWidget(inventory_button)
        self.setLayout(layout)
        self.medicines_data = []

    def open_add_medicine_window(self):
        self.add_medicine_window = AddMedicineWindow(self)
        self.add_medicine_window.show()

    def open_schedule_window(self):
        self.schedule_window = ScheduleWindow(self.medicines_data)
        self.schedule_window.show()

    def open_inventory_window(self):
        QMessageBox.information(self, "Запасы лекарств", "В разработке!")


class AddMedicineWindow(QWidget):
    def __init__(self, main_window):
        super().__init__()
        self.setWindowTitle("Добавить лекарство")
        self.setGeometry(100, 100, 300, 200)
        self.main_window = main_window
        self.medicines = ["Парацетамол", "Аспирин", "Ибупрофен"]
        medicine_label = QLabel("Лекарство:")
        self.medicine_combobox = QComboBox()
        self.medicine_combobox.addItems(self.medicines)
        dosage_label = QLabel("Дозировка:")
        self.dosage_edit = QLineEdit()
        date_label = QLabel("Дата:")
        self.date_edit = QDateEdit()
        time_label = QLabel("Время:")
        self.time_edit = QTimeEdit()
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
        self.main_window.medicines_data.append(
            {"name": medicine_name, "dosage": dosage, "date": date, "time": time}
        )
        self.close()

class ScheduleWindow(QWidget):
    def __init__(self, medicines_data):
        super().__init__()
        self.setWindowTitle("График приема")
        self.setGeometry(100, 100, 400, 300)
        self.medicines_data = medicines_data
        self.selected_row = None
        self.schedule_table = QTableWidget()
        self.schedule_table.setColumnCount(4)
        self.schedule_table.setHorizontalHeaderLabels(["Лекарство", "Дозировка", "Дата", "Время"])
        self.schedule_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.schedule_table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
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
        layout.addWidget(self.schedule_table)
        button_layout = QHBoxLayout()
        button_layout.addWidget(self.delete_button)
        button_layout.addWidget(self.edit_button)
        button_layout.addWidget(self.repeat_button)
        layout.addLayout(button_layout)
        self.setLayout(layout)
        self.schedule_table.selectionModel().selectionChanged.connect(self.handle_selection_changed)
        self.update_table()

    def update_table(self):
        self.schedule_table.setRowCount(0)
        for i, medicine in enumerate(self.medicines_data):
            self.schedule_table.insertRow(i)
            self.schedule_table.setItem(i, 0, QTableWidgetItem(medicine["name"]))
            self.schedule_table.setItem(i, 1, QTableWidgetItem(medicine["dosage"]))
            self.schedule_table.setItem(i, 2, QTableWidgetItem(medicine["date"]))
            self.schedule_table.setItem(i, 3, QTableWidgetItem(medicine["time"]))

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
                del self.medicines_data[row]
                self.update_table()

    def edit_medicine(self):
        selected_rows = self.schedule_table.selectionModel().selectedRows()
        if selected_rows:
            row = selected_rows[0].row()
            self.edit_dialog = EditMedicineDialog(self.medicines_data[row])
            self.edit_dialog.setWindowTitle("Редактировать событие")
            self.edit_dialog.data_changed.connect(self.update_data)
            self.edit_dialog.show()

    def update_data(self, medicine_data):
        selected_rows = self.schedule_table.selectionModel().selectedRows()
        if selected_rows:
            row = selected_rows[0].row()
            self.medicines_data[row] = medicine_data
        self.update_table()

    def open_repeat_dialog(self):
        self.repeat_dialog = RepeatDialog(self)
        self.repeat_dialog.show()
        self.repeat_dialog.repeat_signal.connect(self.repeat_medicine)

    def repeat_medicine(self, repeat_values):
        if self.selected_row is not None:
            medicine = self.medicines_data[self.selected_row]
            days = repeat_values["days"]
            hours = repeat_values["hours"]
            minutes = repeat_values["minutes"]
            date_obj = QDate.fromString(medicine["date"], "yyyy-MM-dd")
            time_obj = QTime.fromString(medicine["time"], "HH:mm")
            time_obj = time_obj.addSecs(minutes * 60 + hours * 3600)
            date_obj = date_obj.addDays(days)
            new_date = date_obj.toString("yyyy-MM-dd")
            new_time = time_obj.toString("HH:mm")
            self.medicines_data.append(
                {
                    "name": medicine["name"],
                    "dosage": medicine["dosage"],
                    "date": new_date,
                    "time": new_time,
                }
            )
            self.update_table()

    def handle_selection_changed(self, selected, deselected):
        self.selected_row = selected.indexes()[0].row() if selected.indexes() else None
        self.repeat_button.setEnabled(self.selected_row is not None)
        self.delete_button.setEnabled(self.selected_row is not None)
        self.edit_button.setEnabled(self.selected_row is not None)

class EditMedicineDialog(QDialog):
    data_changed = pyqtSignal(dict)

    def __init__(self, medicine_data):
        super().__init__()
        self.setWindowTitle("Редактировать событие")
        self.setGeometry(100, 100, 300, 200)
        self.medicines = ["Парацетамол", "Аспирин", "Ибупрофен"]
        medicine_label = QLabel("Лекарство:")
        self.medicine_combobox = QComboBox()
        self.medicine_combobox.addItems(self.medicines)
        self.medicine_combobox.setCurrentText(medicine_data["name"])
        dosage_label = QLabel("Дозировка:")
        self.dosage_edit = QLineEdit(medicine_data["dosage"])
        date_label = QLabel("Дата:")
        self.date_edit = QDateEdit()
        self.date_edit.setDate(QDate.fromString(medicine_data["date"], "yyyy-MM-dd"))
        time_label = QLabel("Время:")
        self.time_edit = QTimeEdit()
        self.time_edit.setTime(QTime.fromString(medicine_data["time"], "HH:mm"))
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
        dosage = self.dosage_edit\
.text()
        date = self.date_edit.date().toString("yyyy-MM-dd")
        time = self.time_edit.time().toString("HH:mm")
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


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
