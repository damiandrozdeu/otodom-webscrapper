import requests
import csv
from bs4 import BeautifulSoup

# URL ogłoszenia
url = "https://www.otodom.pl/pl/oferta/mieszkanie-4-pok-20min-do-centrum-gdanska-ID4tVuh"

# Nagłówki, aby uniknąć blokady przez serwer
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36"
}

# Pobranie strony
response = requests.get(url, headers=headers)

# Sprawdzenie poprawnego pobrania
if response.status_code == 200:
    soup = BeautifulSoup(response.text, "html.parser")

    # Pobranie podstawowych danych
    title = soup.find("h1")
    title_text = title.text.strip() if title else "Tytuł nie znaleziony"

    # Pobranie ceny
    price_tag = soup.find("strong", {"data-cy": "adPageHeaderPrice"})
    price = price_tag.text.strip() if price_tag else "Cena nieznana"

    # Pobranie lokalizacji
    location_tag = soup.find("a", class_="css-1jjm9oe")
    location = location_tag.text.strip() if location_tag else "Lokalizacja nieznana"

    # Pobranie metrażu
    size_tag = soup.find("div", class_="css-1ftqasz")
    size = size_tag.text.strip() if size_tag else "Metraż nieznany"

    # Pobranie piętra
    floor = "Piętro nieznane"
    info_sections = soup.find_all("div", class_="css-1xw0jqp eows69w1")
    for section in info_sections:
        label = section.find("p", class_="eows69w2 css-1airkmu")
        if label and "Piętro" in label.text:
            floor_value = label.find_next_sibling("p", class_="eows69w2 css-1airkmu")
            if floor_value:
                floor = f"='{floor_value.text.strip()}"  # Dodanie apostrofu
            break

    # Pobranie dodatkowych informacji
    details = {}
    for item in soup.find_all("div", class_="css-1xw0jqp"):
        label = item.find("p", class_="eows69w2")
        value = item.find_all("p", class_="eows69w2")[-1]
        if label and value:
            details[label.text.strip().replace(":", "")] = value.text.strip()

    heating = details.get("Ogrzewanie", "Brak danych")
    rent = details.get("Czynsz", "Brak danych")
    finish_state = details.get("Stan wykończenia", "Brak danych")
    market = details.get("Rynek", "Brak danych")
    ownership = details.get("Forma własności", "Brak danych")
    available_from = details.get("Dostępne od", "Brak danych")
    advertiser_type = details.get("Typ ogłoszeniodawcy", "Brak danych")
    
    # Informacje dodatkowe
    additional_info_list = [item.text.strip() for item in soup.find_all("span", class_="css-axw7ok")]
    additional_info = " ".join(additional_info_list) if additional_info_list else "Brak danych"

    build_year = details.get("Rok budowy", "Brak danych")
    elevator = details.get("Winda", "Brak danych")
    building_type = details.get("Rodzaj zabudowy", "Brak danych")
    building_material = details.get("Materiał budynku", "Brak danych")
    windows = details.get("Okna", "Brak danych")
    utilities = details.get("Media", "Brak danych")

    # Zapis do pliku CSV
    csv_file = "dane_mieszkania.csv"
    with open(csv_file, "w", newline="", encoding="utf-8-sig") as file:
        writer = csv.writer(file)
        writer.writerow([
            "Tytuł", "Cena", "Lokalizacja", "Metraż", "Piętro", 
            "Ogrzewanie", "Czynsz", "Stan wykończenia", "Rynek", "Forma własności", "Dostępne od", 
            "Typ ogłoszeniodawcy", "Informacje dodatkowe", "Rok budowy", "Winda", "Rodzaj zabudowy", 
            "Materiał budynku", "Okna", "Media", "Opis"
        ])
        writer.writerow([
            title_text, price, location, size, floor,
            heating, rent, finish_state, market, ownership, available_from,
            advertiser_type, additional_info, build_year, elevator, building_type,
            building_material, windows, utilities
        ])

    print(f"Dane zapisane do pliku: {csv_file}")

else:
    print(f"Błąd pobierania strony, kod statusu: {response.status_code}")

# from selenium import webdriver
# from selenium.webdriver.chrome.service import Service
# from webdriver_manager.chrome import ChromeDriverManager
# from selenium.webdriver.common.by import By
# from selenium.webdriver.support.ui import WebDriverWait
# from selenium.webdriver.support import expected_conditions as EC
# from selenium.common.exceptions import TimeoutException
# from bs4 import BeautifulSoup
# import time

# # 1. Inicjalizacja przeglądarki (Chrome).
# options = webdriver.ChromeOptions()
# # options.add_argument("--headless")  # Odkomentuj, jeśli chcesz tryb headless

# driver = webdriver.Chrome(
#     service=Service(ChromeDriverManager().install()),
#     options=options
# )

# url = "https://www.otodom.pl/pl/oferta/mieszkanie-4-pok-20min-do-centrum-gdanska-ID4tVuh"
# driver.get(url)

# # 2. Poczekaj, aż pojawi się kontener opisu (aby strona zdążyła się załadować).
# wait = WebDriverWait(driver, 5)
# try:
#     wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "div[data-cy='adPageAdDescription']")))
# except TimeoutException:
#     print("Nie udało się odnaleźć kontenera z opisem w rozsądnym czasie.")

# # 3. Spróbuj kliknąć w przycisk "Pokaż więcej" (może go nie być na tej stronie).
# try:
#     show_more_btn = driver.find_element(By.XPATH, "//button[contains(text(),'Pokaż więcej')]")
#     show_more_btn.click()
#     time.sleep(2)  # Można zastąpić WebDriverWait, jeśli potrzeba
# except:
#     # Brak przycisku lub nie udało się kliknąć - nie szkodzi.
#     pass

# # 4. Teraz pobieramy finalny HTML i wyciągamy opis.
# page_source = driver.page_source
# driver.quit()

# soup = BeautifulSoup(page_source, "html.parser")
# description_div = soup.find("div", {"data-cy": "adPageAdDescription"})

# if description_div:
#     description_text = description_div.get_text(separator="\n", strip=True)
#     print(description_text)
# else:
#     print("Opis nie znaleziony.")


