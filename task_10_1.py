from collections import UserDict
import re
from datetime import datetime, date
from typing import List, Optional, Tuple, Callable, Any

# --------------------------
# Базові класи
# --------------------------
class Field:
    def __init__(self, value: Any) -> None:
        self.value: Any = value

    def __str__(self) -> str:
        return str(self.value)


class Name(Field):
    pass


class Phone(Field):
    def __init__(self, value: str) -> None:
        if not re.fullmatch(r"\d{10}", value):
            raise ValueError("Phone number must be exactly 10 digits")
        super().__init__(value)


class Birthday(Field):
    def __init__(self, value: str) -> None:
        try:
            date_obj: date = datetime.strptime(value, "%d.%m.%Y").date()
            super().__init__(date_obj)
        except ValueError:
            raise ValueError("Invalid date format. Use DD.MM.YYYY")

    def __str__(self) -> str:
        return self.value.strftime("%d.%m.%Y")


# --------------------------
# Клас Record
# --------------------------
class Record:
    def __init__(self, name: str) -> None:
        self.name: Name = Name(name)
        self.phones: List[Phone] = []
        self.birthday: Optional[Birthday] = None

    def add_phone(self, phone_value: str) -> None:
        self.phones.append(Phone(phone_value))

    def remove_phone(self, phone_value: str) -> None:
        self.phones = [p for p in self.phones if p.value != phone_value]

    def edit_phone(self, old_value: str, new_value: str) -> bool:
        for i, p in enumerate(self.phones):
            if p.value == old_value:
                self.phones[i] = Phone(new_value)
                return True
        return False

    def find_phone(self, phone_value: str) -> Optional[str]:
        for p in self.phones:
            if p.value == phone_value:
                return p.value
        return None

    def add_birthday(self, birthday_str: str) -> None:
        self.birthday = Birthday(birthday_str)

    def days_to_birthday(self) -> Optional[int]:
        if not self.birthday:
            return None
        today: date = date.today()

        try:
            next_bday: date = self.birthday.value.replace(year=today.year)
        except ValueError:
            next_bday = date(today.year, 2, 28)

        if next_bday < today:
            try:
                next_bday = self.birthday.value.replace(year=today.year + 1)
            except ValueError:
                next_bday = date(today.year + 1, 2, 28)

        return (next_bday - today).days

    def __str__(self) -> str:
        phones_str: str = "; ".join(p.value for p in self.phones)
        bday_str: str = f", birthday: {self.birthday}" if self.birthday else ""
        return f"{self.name.value}: {phones_str}{bday_str}"


# --------------------------
# Клас AddressBook
# --------------------------
class AddressBook(UserDict[str, Record]):

    def add_record(self, record: Record) -> None:
        self.data[record.name.value] = record

    def find(self, name_value: str) -> Optional[Record]:
        return self.data.get(name_value)

    def delete(self, name_value: str) -> None:
        if name_value in self.data:
            del self.data[name_value]

    def get_upcoming_birthdays(self) -> List[Tuple[str, date]]:
        today: date = date.today()
        upcoming: List[Tuple[str, date]] = []

        for record in self.data.values():
            if record.birthday:
                bday: date = record.birthday.value

                try:
                    next_bday: date = bday.replace(year=today.year)
                except ValueError:
                    next_bday = date(today.year, 2, 28)

                if next_bday < today:
                    try:
                        next_bday = bday.replace(year=today.year + 1)
                    except ValueError:
                        next_bday = date(today.year + 1, 2, 28)

                days_until: int = (next_bday - today).days
                if 0 <= days_until <= 7:
                    upcoming.append((record.name.value, next_bday))

        return sorted(upcoming, key=lambda x: x[1])


# --------------------------
# Декоратор обробки помилок
# --------------------------
def input_error(func: Callable) -> Callable:
    def inner(*args: Any, **kwargs: Any) -> str:
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
def parse_input(user_input: str) -> Tuple[str, List[str]]:
    parts: List[str] = user_input.strip().split()
    command: str = parts[0].lower()
    args: List[str] = parts[1:]
    return command, args


# --------------------------
# Функції обробки команд
# --------------------------
@input_error
def add_contact(args: List[str], book: AddressBook) -> str:
    name, phone, *_ = args
    record: Optional[Record] = book.find(name)
    message: str = "Contact updated."

    if record is None:
        record = Record(name)
        book.add_record(record)
        message = "Contact added."

    if phone:
        record.add_phone(phone)
    return message


@input_error
def change_contact(args: List[str], book: AddressBook) -> str:
    name, old_phone, new_phone, *_ = args
    record: Optional[Record] = book.find(name)
    if not record:
        raise KeyError

    if record.edit_phone(old_phone, new_phone):
        return "Phone updated."
    return "Old phone not found."


@input_error
def show_phone(args: List[str], book: AddressBook) -> str:
    name: str = args[0]
    record: Optional[Record] = book.find(name)
    if not record:
        raise KeyError
    if not record.phones:
        return "No phones for this contact."
    return ", ".join(p.value for p in record.phones)


@input_error
def show_all(book: AddressBook) -> str:
    if not book.data:
        return "No contacts."
    return "\n".join(str(record) for record in book.data.values())


@input_error
def add_birthday(args: List[str], book: AddressBook) -> str:
    name, bday = args
    record: Optional[Record] = book.find(name)
    if not record:
        raise KeyError
    record.add_birthday(bday)
    return f"Birthday added for {name}."


@input_error
def show_birthday(args: List[str], book: AddressBook) -> str:
    name: str = args[0]
    record: Optional[Record] = book.find(name)
    if not record:
        raise KeyError
    if not record.birthday:
        return "No birthday set."
    return f"{name}'s birthday: {record.birthday}"


@input_error
def birthdays(args: List[str], book: AddressBook) -> str:
    upcoming: List[Tuple[str, date]] = book.get_upcoming_birthdays()
    if not upcoming:
        return "No upcoming birthdays."
    return "\n".join(f"{name}: {bday.strftime('%d.%m.%Y')}" for name, bday in upcoming)


# --------------------------
# Основний цикл бота
# --------------------------
def main() -> None:
    book: AddressBook = AddressBook()
    print("Welcome to the assistant bot!")

    while True:
        user_input: str = input(">>> ")
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
    gfdgfdgfdfg
    hdfhgfdhdfhfgh
    hgfhgfhgfhg