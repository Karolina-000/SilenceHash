"""
BookHash - წიგნზე დაფუძნებული ჰაშინგი (კრავთა დუმილი)

იდეა: წიგნი არის საიდუმლო "გასაღები". პაროლის თითოეული სიმბოლო
გვიშვებს წიგნის რომელიმე გვერდზე და ამ გვერდის ტექსტი ერევა ჰაშში.
ვისაც ზუსტად იგივე წიგნის ფაილი არ აქვს, იგივე ჰაშს ვერ მიიღებს.
"""

import hashlib
import json
import os

# წიგნის ფაილი: შეიძლება იყოს PDF (გვერდები ნამდვილი იქნება) ან TXT (1500 სიმბოლო = 1 გვერდი)
BOOK_FILES = ["book.pdf", "book.txt"]
USERS_FILE = "users.json"   # აქ ინახება მომხმარებლები და მათი ჰაშები
PAGE_SIZE = 1500            # რამდენი სიმბოლოა ერთ "გვერდზე"

# PEPPER - საერთო საიდუმლო ტექსტი. salt-ისგან განსხვავებით, ის users.json-ში არ ინახება!
PEPPER = "8ay"


def clean(text):
    """ზედმეტ ჰარებს და ახალ ხაზებს ვასუფთავებთ, რომ ფორმატირებამ არ იმოქმედოს."""
    return " ".join(text.split())


def load_pages_pdf(filename):
    """კითხულობს PDF-ს: თითო ნამდვილი გვერდი = თითო 'გვერდი' ჰაშისთვის."""
    from pypdf import PdfReader   # pip install pypdf

    reader = PdfReader(filename)
    pages = []
    for page in reader.pages:
        text = clean(page.extract_text() or "")
        if text:                  # ცარიელ გვერდებს (სურათები და ა.შ.) ვტოვებთ
            pages.append(text)
    return pages


def load_pages_txt(filename, page_size=PAGE_SIZE):
    """კითხულობს TXT-ს და ჭრის გვერდებად."""
    with open(filename, "r", encoding="utf-8") as f:
        text = clean(f.read())

    pages = []
    for i in range(0, len(text), page_size):
        pages.append(text[i:i + page_size])
    return pages


def find_book():
    """ეძებს წიგნის ფაილს პროგრამის გვერდით."""
    for name in BOOK_FILES:
        if os.path.exists(name):
            return name
    return None


def load_pages(filename):
    if filename.lower().endswith(".pdf"):
        return load_pages_pdf(filename)
    return load_pages_txt(filename)


def book_hash(message, pages, salt=""):
    """
    აბრუნებს message-ის BookHash-ს (64 სიმბოლოიანი ჰექს-სტრიქონი).
    salt - შემთხვევითი დამატება, რომ ერთნაირი პაროლები სხვადასხვა ჰაშს იძლეოდეს.
    """
    data = salt + message

    # საწყისი მდგომარეობა (აქ ვურევთ PEPPER-საც)
    state = hashlib.sha256((PEPPER + data).encode("utf-8")).digest()

    for position, char in enumerate(data):
        # ვთვლით, რომელ გვერდზე უნდა გადავიდეთ
        seed = int.from_bytes(state, "big") + ord(char) * (position + 1)
        page_number = seed % len(pages)
        page_text = pages[page_number]

        # ვურევთ გვერდის ტექსტს მდგომარეობაში
        state = hashlib.sha256(
            state + page_text.encode("utf-8") + str(page_number).encode()
        ).digest()

    return state.hex()


# ---------- მომხმარებლების შენახვა ----------

def load_users():
    if not os.path.exists(USERS_FILE):
        return {}
    with open(USERS_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def save_users(users):
    with open(USERS_FILE, "w", encoding="utf-8") as f:
        json.dump(users, f, indent=2)


def register(pages):
    users = load_users()
    username = input("მომხმარებლის სახელი: ")
    if username in users:
        print("ასეთი მომხმარებელი უკვე არსებობს.")
        return
    password = input("პაროლი: ")

    salt = os.urandom(8).hex()  # შემთხვევითი salt
    users[username] = {"salt": salt, "hash": book_hash(password, pages, salt)}
    save_users(users)
    print("რეგისტრაცია დასრულდა. ჰაში:", users[username]["hash"])


def login(pages):
    users = load_users()
    username = input("მომხმარებლის სახელი: ")
    password = input("პაროლი: ")

    if username not in users:
        print("მომხმარებელი ვერ მოიძებნა.")
        return

    salt = users[username]["salt"]
    if book_hash(password, pages, salt) == users[username]["hash"]:
        print("შესვლა წარმატებულია!")
    else:
        print("პაროლი არასწორია.")


def main():
    book = find_book()
    if book is None:
        print("ვერ ვიპოვე წიგნი. ჩააგდე 'book.pdf' ან 'book.txt' ამ პროგრამის გვერდით.")
        return

    pages = load_pages(book)
    if len(pages) == 0:
        print("წიგნიდან ტექსტი ვერ ამოვიკითხე (შეიძლება PDF სკანირებული სურათებია).")
        return
    print(f"წიგნი ჩაიტვირთა ({book}): {len(pages)} გვერდი")

    while True:
        print("\n1 - რეგისტრაცია\n2 - შესვლა\n3 - ტექსტის დაჰაშვა\n0 - გასვლა")
        choice = input("არჩევანი: ")

        if choice == "1":
            register(pages)
        elif choice == "2":
            login(pages)
        elif choice == "3":
            text = input("ტექსტი: ")
            salt = os.urandom(8).hex()
            print("BookHash:", book_hash(text, pages, salt))
        elif choice == "0":
            break


if __name__ == "__main__":
    main()