import datetime

import telebot
from telebot import types

import yandex_geocoder

import yoomoney
from yoomoney import Quickpay

from gspread import Spreadsheet, service_account, Worksheet


# токен для нашего телеграм бота
API_BOT_TOKEN: str = "YOUR_TOKEN_FOR_TG_BOT"
# =====================================================================================================================

# ключ для работы с Яндекс картой
API_KEY_YANDEX_FOR_MAPS: str = "YOUR_API_KEY_FOR_YANDEX_MAPS"

# константы для поиска адреса
CITY: str = "Казань"
STREET: str = "Ленина"
HOUSE: str = "1"
# =====================================================================================================================

# токен для работы с Юмани
ACCESS_TOKEN: str = "YOUR_ACCESS_TOKEN_FOR_YOOMONEY"

# сумма для отправки
TOTAL_FOR_PAY: int = 2
# =====================================================================================================================

# Путь к картинке
IMAGE_PATH: str = "img1.JPG"
# =====================================================================================================================

# id гугл таблички для подключения
TABLE_ID: str = "YOUR_TABLE_ID_FOR_GOOGLE_SHEETS"

# имя листа с которым мы работаем
WORKSHEET_TITLE = "Sheet1"

# строка и столбец для получения значения из гугл таблицы
COLUMN_FOR_GET: str = "A"
ROW_FOR_GET: int = 2

# строка и столбец для изменения значения из гугл таблицы
COLUMN_FOR_SET: str = "B"
ROW_FOR_SET: int = 2
# =====================================================================================================================

bot: any = telebot.TeleBot(API_BOT_TOKEN)


@bot.message_handler(commands=['start'])  # создаем команду
def start(message: any) -> None:
    """Создание кнопок согласно ТЗ"""

    markup: any = types.InlineKeyboardMarkup()

    # кнопка 1: ссылка с текстом на Яндекс карту
    button1: any = types.InlineKeyboardButton(f"Город {CITY}, улица {STREET}, {HOUSE}",
                                              url=create_link_to_yandex_maps(CITY, STREET, HOUSE))
    markup.add(button1)

    # кнопка 2: ссылка на оплату через Юмани, в размере 2 р.
    payment: str = yoomoney_payment()
    button2: any = types.InlineKeyboardButton("Ссылка на оплату в размере 2 р.", url=payment)
    markup.add(button2)

    # кнопка 3: при нажатии получаем картинку с текстом
    button3: any = types.InlineKeyboardButton("Картинка с текстом", callback_data='image_with_text')
    markup.add(button3)

    # кнопка 4: получаем значение ячейки из гугл таблички
    button4: any = types.InlineKeyboardButton("Получить значение из гугл таблички",
                                              callback_data="get_value_from_google_sheets")
    markup.add(button4)

    bot.send_message(message.chat.id,
                     f"Привет, {message.from_user.first_name} :) Нажмите на кнопки, или введите дату (в формате "
                     f"дд.мм.гггг) для записи на гугл табличку",
                     reply_markup=markup)


@bot.message_handler(content_types=['text'])
def handle_message(message: any) -> None:
    """Получение сообщения и проверки корректности даты"""
    text = check_date(message.text)

    if text != message.text:
        bot.send_message(message.chat.id, text)
    else:
        bot.send_message(message.chat.id, "Дата сохранена")


@bot.callback_query_handler(func=lambda call: True)
def callback_inline(call: any) -> None:
    """Колбек функция для выполнения при нажатии кнопки"""
    if call.data == 'image_with_text':
        # отправка картинки
        chat_id: int | str = call.message.chat.id
        img: any = open(IMAGE_PATH, 'rb')
        bot.send_photo(chat_id, img, caption="Текст к изображению")
        img.close()
    elif call.data == "get_value_from_google_sheets":
        # отправка полученного значения из гугл таблички
        chat_id: int | str = call.message.chat.id
        bot.send_message(chat_id, get_value_by_row_and_column(COLUMN_FOR_GET, ROW_FOR_GET))


def create_link_to_yandex_maps(city: str, street: str, house: str) -> str:
    """Создание ссылки на Яндекс карту через название города, улицы и номера дома"""
    client: any = yandex_geocoder.Client(API_KEY_YANDEX_FOR_MAPS)
    coordinates: tuple = client.coordinates(f"{city} {street} {house}")
    url: str = f"https://yandex.ru/maps/?pt={str(coordinates[0])},{str(coordinates[1])}&z=16&l=map"
    return url


def yoomoney_payment() -> str:
    """Создание ссылки на оплату через Юмани"""
    client: any = yoomoney.Client(ACCESS_TOKEN)
    user: any = client.account_info()
    quickpay: any = Quickpay(
        receiver=user.account,
        quickpay_form="shop",
        targets="Sponsor this project",
        paymentType="SB",
        sum=TOTAL_FOR_PAY,
    )
    return quickpay.redirected_url


def client_init_json() -> any:
    """Создание клиента для работы с Google Sheets."""
    return service_account(filename='testtgbot.json')


def get_table_by_id(client: any, table_url: str) -> Spreadsheet:
    """Получение таблицы из Google Sheets по ID таблицы."""
    return client.open_by_key(table_url)


def update_value_by_row_and_column(data: list, row: int, column: str) -> bool:
    """Вставка данных в ячейку листа гугл таблички"""
    client: any = client_init_json()
    table: Spreadsheet = get_table_by_id(client, TABLE_ID)
    try:
        worksheet: Worksheet = table.worksheet(WORKSHEET_TITLE)
        worksheet.update(data, f'{column}{str(row)}')
        return True
    except Exception as e:
        print(e)
        return False


def get_value_by_row_and_column(column: str, row: int) -> str:
    """Получение данных из ячейки листа гугл таблички"""
    client: any = client_init_json()
    table: Spreadsheet = get_table_by_id(client, TABLE_ID)
    try:
        worksheet: Worksheet = table.worksheet(WORKSHEET_TITLE)
        value: str = worksheet.acell(column + str(row)).value
        return value
    except Exception as e:
        print(e)
        return "Не получилось получить данные из гугл таблицы"


def check_date(message: str) -> str:
    """Проверка формата даты"""
    try:
        date_format: str = "%d.%m.%Y"
        datetime.datetime.strptime(message, date_format)
        if not update_value_by_row_and_column([[message]], row=ROW_FOR_SET, column=COLUMN_FOR_SET):
            message = "Дата введена неверно"
    except ValueError:
        print(message)
        message = "Дата введена неверно"
    return message


def main() -> None:
    """Основная функция (точка входа)"""
    bot.polling(none_stop=True)


if __name__ == "__main__":
    main()
