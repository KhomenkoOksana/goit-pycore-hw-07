from collections import UserDict
import re
from datetime import datetime, timedelta, date

# --------------------------
# Базові класи
# --------------------------
class Field:
    def __init__(self, value):
        self.value = value

    def __str__(self):
        return str(self.value)

class Name(Field):
    pass

class Phone(Field):
    def __init__(self, value):
        if not re.fullmatch(r"\d{10}", value):
            raise ValueError("Phone number must be exactly 10 digits")
        super().__init__(value)

class Birthday(Field):
    def __init__(self, value):
        try:
            date_obj = datetime.strptime(value, "%d.%m.%Y").date()
            super().__init__(date_obj)
        except ValueError:
            raise ValueError("Invalid date format. Use DD.MM.YYYY")

    def __str__(self):
        return self.value.strftime("%d.%m.%Y")

# --------------------------
# Клас Record
# --------------------------
class Record:
    def __init__(self, name):
        self.name = Name(name)
        self.phones = []
        self.birthday = None

    def add_phone(self, phone_value):
        self.phones.append(Phone(phone_value))

    def remove_phone(self, phone_value):
        self.phones = [p for p in self.phones if p.value != phone_value]

    def edit_phone(self, old_value, new_value):
        for i, p in enumerate(self.phones):
            if p.value == old_value:
                self.phones[i] = Phone(new_value)
                return True
        return False

    def find_phone(self, phone_value):
        for p in self.phones:
            if p.value == phone_value:
                return p.value
        return None

    def add_birthday(self, birthday_str):
        self.birthday = Birthday(birthday_str)

    def days_to_birthday(self):
        if not self.birthday:
            return None
        today = date.today()
        next_bday = self.birthday.value.replace(year=today.year)
        if next_bday < today:
            next_bday = next_bday.replace(year=today.year + 1)
        return (next_bday - today).days

    def __str__(self):
        phones_str = "; ".join(p.value for p in self.phones)
        bday_str = f", birthday: {self.birthday}" if self.birthday else ""
        return f"{self.name.value}: {phones_str}{bday_str}"

# --------------------------
# Клас AddressBook
# --------------------------
class AddressBook(UserDict):
    def add_record(self, record: Record):
        self.data[record.name.value] = record

    def find(self, name_value):
        return self.data.get(name_value, None)

    def delete(self, name_value):
        if name_value in self.data:
            del self.data[name_value]

    def get_upcoming_birthdays(self):
        today = date.today()
        upcoming = []
        for record in self.data.values():
            if record.birthday:
                next_bday = record.birthday.value.replace(year=today.year)
                if next_bday < today:
                    next_bday = next_bday.replace(year=today.year + 1)
                days_until = (next_bday - today).days
                if 0 <= days_until <= 7:
                    upcoming.append((record.name.value, next_bday))
        return sorted(upcoming, key=lambda x: x[1])

# --------------------------
# Декоратор обробки помилок
# --------------------------
def input_error(func):
    def inner(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except IndexError:
            return "Enter user name."
        except KeyError:
            return "Contact not found."
        except ValueError as ve:
            return str(ve)
    return inner

# --------------------------
# Парсер команд
# --------------------------
def parse_input(user_input):
    parts = user_input.strip().split()
    command = parts[0].lower()
    args = parts[1:]
    return command, args

# --------------------------
# Функції обробки команд
# --------------------------
@input_error
def add_contact(args, book: AddressBook):
    name, phone, *_ = args
    record = book.find(name)
    message = "Contact updated."
    if record is None:
        record = Record(name)
        book.add_record(record)
        message = "Contact added."
    if phone:
        record.add_phone(phone)
    return message

@input_error
def change_contact(args, book: AddressBook):
    name, old_phone, new_phone, *_ = args
    record = book.find(name)
    if not record:
        raise KeyError
    if record.edit_phone(old_phone, new_phone):
        return "Phone updated."
    return "Old phone not found."

@input_error
def show_phone(args, book: AddressBook):
    name = args[0]
    record = book.find(name)
    if not record:
        raise KeyError
    if not record.phones:
        return "No phones for this contact."
    return ", ".join(p.value for p in record.phones)

@input_error
def show_all(book: AddressBook):
    if not book.data:
        return "No contacts."
    return "\n".join(str(record) for record in book.data.values())

@input_error
def add_birthday(args, book: AddressBook):
    name, bday = args
    record = book.find(name)
    if not record:
        raise KeyError
    record.add_birthday(bday)
    return f"Birthday added for {name}."

@input_error
def show_birthday(args, book: AddressBook):
    name = args[0]
    record = book.find(name)
    if not record:
        raise KeyError
    if not record.birthday:
        return "No birthday set."
    return f"{name}'s birthday: {record.birthday}"

@input_error
def birthdays(args, book: AddressBook):
    upcoming = book.get_upcoming_birthdays()
    if not upcoming:
        return "No upcoming birthdays."
    return "\n".join(f"{name}: {bday.strftime('%d.%m.%Y')}" for name, bday in upcoming)

# --------------------------
# Основний цикл бота
# --------------------------
def main():
    book = AddressBook()
    print("Welcome to the assistant bot!")

    while True:
        user_input = input(">>> ")
        command, args = parse_input(user_input)

        if command in ["close", "exit"]:
            print("Good bye!")
            break
        elif command == "hello":
            print("How can I help you?")
        elif command == "add":
            print(add_contact(args, book))
        elif command == "change":
            print(change_contact(args, book))
        elif command == "phone":
            print(show_phone(args, book))
        elif command == "all":
            print(show_all(book))
        elif command == "add-birthday":
            print(add_birthday(args, book))
        elif command == "show-birthday":
            print(show_birthday(args, book))
        elif command == "birthdays":
            print(birthdays(args, book))
        else:
            print("Invalid command.")

if __name__ == "__main__":
    main()