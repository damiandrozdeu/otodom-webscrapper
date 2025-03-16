import requests
from bs4 import BeautifulSoup
import csv
import time
import concurrent.futures

# Importy Selenium
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException

def extract_description_selenium(link, driver):
    """
    Funkcja używa Selenium do pobrania opisu oferty.
    """
    driver.get(link)
    wait = WebDriverWait(driver, 5)
    try:
        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "div[data-cy='adPageAdDescription']")))
    except TimeoutException:
        print(f"Nie udało się odnaleźć kontenera z opisem dla: {link}")
        return "Brak opisu"
    
    # Kliknij przycisk "Pokaż więcej", jeśli jest dostępny
    try:
        show_more_btn = driver.find_element(By.XPATH, "//button[contains(text(),'Pokaż więcej')]")
        show_more_btn.click()
        time.sleep(2)  # krótkie oczekiwanie, by zawartość się rozwinęła
    except Exception:
        pass
    
    page_source = driver.page_source
    soup = BeautifulSoup(page_source, "html.parser")
    description_div = soup.find("div", {"data-cy": "adPageAdDescription"})
    
    if description_div:
        return description_div.get_text(separator="\n", strip=True)
    else:
        return "Brak opisu"

def extract_detailed_info(link, headers, driver):
    """
    Pobiera dane oferty przy użyciu requests/BeautifulSoup dla większości elementów 
    oraz Selenium dla pobrania pełnego opisu.
    """
    response = requests.get(link, headers=headers)
    if response.status_code != 200:
        print(f"Błąd pobierania strony oferty: {link}")
        return None

    soup = BeautifulSoup(response.text, "html.parser")
    
    # Podstawowe dane
    title_tag = soup.find("h1")
    title_text = title_tag.text.strip() if title_tag else "Tytuł nie znaleziony"

    price_tag = soup.find("strong", {"data-cy": "adPageHeaderPrice"})
    price = price_tag.text.strip() if price_tag else "Cena nieznana"

    location_tag = soup.find("a", class_="css-1jjm9oe")
    location = location_tag.text.strip() if location_tag else "Lokalizacja nieznana"

    size_tag = soup.find("div", class_="css-1ftqasz")
    size = size_tag.text.strip() if size_tag else "Metraż nieznany"

    # Pobranie informacji o piętrze
    floor = "Piętro nieznane"
    info_sections = soup.find_all("div", class_="css-1xw0jqp eows69w1")
    for section in info_sections:
        label = section.find("p", class_="eows69w2 css-1airkmu")
        if label and "Piętro" in label.text:
            floor_value = label.find_next_sibling("p", class_="eows69w2 css-1airkmu")
            if floor_value:
                # Zachowujemy stały znak "='"
                floor = f"='{floor_value.text.strip()}"
            break

    # Pobranie dodatkowych szczegółów
    details = {}
    for item in soup.find_all("div", class_="css-1xw0jqp"):
        label = item.find("p", class_="eows69w2")
        value_tags = item.find_all("p", class_="eows69w2")
        if label and value_tags:
            value = value_tags[-1].text.strip()
            details[label.text.strip().replace(":", "")] = value

    heating = details.get("Ogrzewanie", "Brak danych")
    rent = details.get("Czynsz", "Brak danych")
    finish_state = details.get("Stan wykończenia", "Brak danych")
    market = details.get("Rynek", "Brak danych")
    ownership = details.get("Forma własności", "Brak danych")
    available_from = details.get("Dostępne od", "Brak danych")
    advertiser_type = details.get("Typ ogłoszeniodawcy", "Brak danych")
    
    additional_info_list = [item.text.strip() for item in soup.find_all("span", class_="css-axw7ok")]
    additional_info = " ".join(additional_info_list) if additional_info_list else "Brak danych"
    
    build_year = details.get("Rok budowy", "Brak danych")
    elevator = details.get("Winda", "Brak danych")
    building_type = details.get("Rodzaj zabudowy", "Brak danych")
    building_material = details.get("Materiał budynku", "Brak danych")
    windows = details.get("Okna", "Brak danych")
    utilities = details.get("Media", "Brak danych")
    
    # Pobranie opisu za pomocą Selenium
    description = extract_description_selenium(link, driver)
    
    return {
        "Tytuł": title_text,
        "Cena": price,
        "Lokalizacja": location,
        "Metraż": size,
        "Piętro": floor,
        "Ogrzewanie": heating,
        "Czynsz": rent,
        "Stan wykończenia": finish_state,
        "Rynek": market,
        "Forma własności": ownership,
        "Dostępne od": available_from,
        "Typ ogłoszeniodawcy": advertiser_type,
        "Informacje dodatkowe": additional_info,
        "Rok budowy": build_year,
        "Winda": elevator,
        "Rodzaj zabudowy": building_type,
        "Materiał budynku": building_material,
        "Okna": windows,
        "Media": utilities,
        "Opis": description,
        "Link": link
    }

def process_listing(link, headers):
    """
    Funkcja przetwarza pojedynczy link oferty.
    Tworzy własny driver, pobiera dane oferty i zamyka driver.
    """
    options = webdriver.ChromeOptions()
    # options.add_argument("--headless")  # odkomentuj, jeśli chcesz pracować w trybie headless
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    
    details = extract_detailed_info(link, headers, driver)
    
    driver.quit()
    return details

def scrape_otodom(start_page, end_page):
    """
    Przegląda strony wyników oraz zbiera dane ze szczegółowych ofert.
    Łączy metodę requests do pobierania listingu z Selenium do pobierania opisu.
    Wersja z optymalizacją – równoległe przetwarzanie ofert przy użyciu ThreadPoolExecutor.
    """
    base_url = "https://www.otodom.pl/pl/wyniki/sprzedaz/mieszkanie/cala-polska?page="
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36"
    }
    
    listing_links = []
    
    # Zbieranie linków do ofert z kolejnych stron wyników
    for page in range(start_page, end_page + 1):
        url = base_url + str(page)
        print(f"Pobieranie strony: {url}")
        response = requests.get(url, headers=headers)
        if response.status_code != 200:
            print(f"Błąd pobierania strony {page}")
            continue
        
        soup = BeautifulSoup(response.text, "html.parser")
        listings = soup.find_all("article", attrs={"data-cy": "listing-item"})
        
        for listing in listings:
            link_tag = listing.find("a", attrs={"data-cy": "listing-item-link"})
            if link_tag:
                full_link = "https://www.otodom.pl" + link_tag["href"]
                # Pobranie liczby pokoi, jeśli dostępna
                rooms_tag = listing.find("dt", string="Liczba pokoi")
                rooms = rooms_tag.find_next_sibling("dd").text.strip() if rooms_tag else "Brak danych"
                listing_links.append((full_link, rooms))
            else:
                print("Brak linku w ofercie.")
        time.sleep(1)
    
    print(f"Znaleziono {len(listing_links)} ofert.")
    all_properties = []
    
    # Równoległe przetwarzanie ofert
    with concurrent.futures.ThreadPoolExecutor(max_workers=15) as executor:
        futures = {executor.submit(process_listing, link, headers): (link, rooms) for (link, rooms) in listing_links}
        for future in concurrent.futures.as_completed(futures):
            result = future.result()
            if result:
                _, rooms = futures[future]
                result["Liczba pokoi"] = rooms
                all_properties.append(result)
                print(f"Przetworzono: {result['Link']}")
    
    # Zapis do pliku CSV
    csv_file = "otodom_listings_detailed.csv"
    with open(csv_file, "w", newline="", encoding="utf-8-sig") as file:
        fieldnames = [
            "Tytuł", "Cena", "Lokalizacja", "Metraż", "Piętro", "Ogrzewanie", "Czynsz",
            "Stan wykończenia", "Rynek", "Forma własności", "Dostępne od", "Typ ogłoszeniodawcy",
            "Informacje dodatkowe", "Rok budowy", "Winda", "Rodzaj zabudowy", "Materiał budynku",
            "Okna", "Media", "Opis", "Liczba pokoi", "Link"
        ]
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()
        for prop in all_properties:
            writer.writerow(prop)
    
    print(f"Dane zapisane do {csv_file}")

if __name__ == "__main__":
    start_page = int(input("Podaj numer początkowej strony: "))
    end_page = int(input("Podaj numer końcowej strony: "))
    scrape_otodom(start_page, end_page)
