import sys
from PyQt6.QtWidgets import (
    QApplication,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QCalendarWidget,
    QTimeEdit,
    QTextEdit,
    QListWidget,
    QPushButton,
)


class MedicineReminder(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Контроль приёма лекарств")

        self.calendar = QCalendarWidget(self)
        self.time_edit = QTimeEdit(self)
        self.medication_description = QTextEdit(self)
        self.event_list = QListWidget(self)
        self.add_button = QPushButton("Добавить", self)

        main_layout = QVBoxLayout()
        top_layout = QHBoxLayout()
        bottom_layout = QHBoxLayout()

        top_layout.addWidget(self.calendar)
        top_layout.addWidget(self.time_edit)
        bottom_layout.addWidget(self.medication_description)
        bottom_layout.addWidget(self.event_list)
        bottom_layout.addWidget(self.add_button)

        main_layout.addLayout(top_layout)
        main_layout.addLayout(bottom_layout)

        self.setLayout(main_layout)

        self.add_button.clicked.connect(self.add_event)
        self.all_dates = {}

    def add_event(self):
        date = self.calendar.selectedDate().toString("yyyy-MM-dd")
        time = self.time_edit.text()
        description = self.medication_description.toPlainText()

        self.all_dates[f'{date} {time}'] = description

        self.medication_description.clear()
        self.event_list.clear()
        for key in sorted(self.all_dates.keys()):
            self.event_list.addItem(f'{key} - {self.all_dates[key]}')


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MedicineReminder()
    window.show()
    sys.exit(app.exec())
