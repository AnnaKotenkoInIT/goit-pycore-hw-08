from collections import UserDict
import re
from datetime import datetime
import pickle

class Field:
    def __init__(self, value):
        self.value = value

    def __str__(self):
        return str(self.value)

class Name(Field):
    def __init__(self, name):
        if not name:
            raise ValueError("Name is a required field")
        super().__init__(name)

class Phone(Field):
    def __init__(self, phone):
        if not isinstance(phone, str) or not re.fullmatch(r"\d{10}", phone):
            raise ValueError("Phone number must be 10 digits")
        super().__init__(phone)

class Birthday(Field):
    def __init__(self, value):
        try:
            self.value = datetime.strptime(value, "%d.%m.%Y").date()
        except ValueError:
            raise ValueError("Invalid date format. Example: DD.MM.YYYY")

    def __str__(self):
        return self.value.strftime("%d.%m.%Y")

class Record:
    def __init__(self, name):
        self.name = Name(name)
        self.phones = []
        self.birthday = None

    def add_phone(self, new_phone):
        if any(p.value == new_phone for p in self.phones):
            raise ValueError("Phone number already exists")
        self.phones.append(Phone(new_phone))

    def remove_phone(self, phone):
        for p in self.phones:
            if p.value == phone:
                self.phones.remove(p)
                return
        raise ValueError("Phone number not found")

    def edit_phone(self, old_phone, new_phone):
        for i, p in enumerate(self.phones):
            if p.value == old_phone:
                self.phones[i] = Phone(new_phone)
                return
        raise ValueError("Old phone number not found")

    def find_phone(self, phone):
        for p in self.phones:
            if p.value == phone:
                return p.value
        raise ValueError("Phone number not found")

    def add_birthday(self, birthday):
        self.birthday = Birthday(birthday)

    def __str__(self):
        phones_str = '; '.join(p.value for p in self.phones)
        birthday_str = f", birthday: {self.birthday}" if self.birthday else ""
        return f"Contact name: {self.name}, phones: {phones_str}{birthday_str}"

class AddressBook(UserDict):
    def add_record(self, record):
        if record.name.value in self.data:
            raise ValueError(f"Record with name '{record.name.value}' already exists")
        self.data[record.name.value] = record

    def find(self, name):
        return self.data.get(name)

    def delete(self, name):
        if name in self.data:
            del self.data[name]
        else:
            raise ValueError("Contact not found")

    def get_upcoming_birthdays(self):
        today = datetime.today().date()
        upcoming_birthdays = []

        for record in self.data.values():
            if record.birthday:
                birthday_this_year = record.birthday.value.replace(year=today.year)

                if birthday_this_year < today:
                    birthday_this_year = birthday_this_year.replace(year=today.year + 1)

                days_to_birthday = (birthday_this_year - today).days

                if 0 <= days_to_birthday <= 7:
                    upcoming_birthdays.append({
                        'name': record.name.value,
                        'congratulation_date': birthday_this_year.strftime('%Y.%m.%d')
                    })

        return upcoming_birthdays

def save_data(book, filename="addressbook.pkl"):
    with open(filename, "wb") as f:
        pickle.dump(book, f)

def load_data(filename="addressbook.pkl"):
    try:
        with open(filename, "rb") as f:
            return pickle.load(f)
    except FileNotFoundError:
        return AddressBook()

# fuctions for the bot
def parse_input(user_input):
    cmd, *args = user_input.split()
    return cmd.strip().lower(), args

def input_error(func):
    def inner(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as error:
            return str(error)
    return inner

@input_error
def add_contact(args, book: AddressBook):
    if len(args) < 2:
        return "Example: add [name] [phone]"
    name, phone = args
    record = book.find(name)

    if not record:
        record = Record(name)
        book.add_record(record)
        message = "Contact added"
    else:
        message = "Contact updated"

    record.add_phone(phone)
    return message

@input_error
def change_contact(args, book: AddressBook):
    if len(args) != 3:
        return "Example: change [name] [old_number] [new_number]"
    name, old_number, new_number = args
    record = book.find(name)

    if not record:
        return "Contact does not exist"
    
    record.edit_phone(old_number, new_number)
    return "Phone changed :)"

@input_error
def show_phone(args, book: AddressBook):
    if len(args) != 1:
        return "Example: phone [name]"
    name = args[0]
    record = book.find(name)

    if not record:
        return "Contact does not exist"
    return record

@input_error
def add_birthday(args, book: AddressBook):
    if len(args) != 2:
        return "Example: add-birthday [name] [date]"
    name, date = args
    record = book.find(name)

    if not record:
        return "Contact does not exist"

    record.add_birthday(date)
    return "Birthday added"

@input_error
def show_birthday(args, book: AddressBook):
    if len(args) != 1:
        return "Example: show-birthday [name]"
    name = args[0]
    record = book.find(name)

    if not record:
        return "Contact does not exist"
    
    return record.birthday or "Birthday not added to this contact"

@input_error
def birthdays(_, book: AddressBook):
    upcoming_birthdays = book.get_upcoming_birthdays()
    if not upcoming_birthdays:
        return "No upcoming birthdays."
    return "\n".join(f"{user['name']} has a birthday on {user['congratulation_date']}" for user in upcoming_birthdays)

# main function for the bot
def main():

    book = load_data()

    print("Welcome to the assistant bot!")

    while True:
        user_input = input("Enter a command: ")
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
            print(book)
        elif command == "add-birthday":
            print(add_birthday(args, book))
        elif command == "show-birthday":
            print(show_birthday(args, book))
        elif command == "birthdays":
            print(birthdays(args, book))
        else:
            print("Invalid command.")

    save_data(book)

if __name__ == "__main__":
    main()

