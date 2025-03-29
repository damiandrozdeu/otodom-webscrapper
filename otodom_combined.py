import requests
from bs4 import BeautifulSoup
import csv
import time
import concurrent.futures
import json
import random
from urllib.parse import urljoin


class OtodomScraper:
    def __init__(self):
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
            "Accept-Language": "pl-PL,pl;q=0.9",
        }
        self.session = requests.Session()
        self.session.headers.update(self.headers)

    @staticmethod
    def safe_get(data, keys, default=None):
        for key in keys:
            try:
                data = data.get(key, {})
            except AttributeError:
                return default
        return data if data not in [None, {}] else default

    def get_characteristics_dict(self, ad_data):
        characteristics = {}
        for item in self.safe_get(ad_data, ['characteristics'], []):
            key = item.get('key')
            if key:
                characteristics[key] = {
                    'value': item.get('value'),
                    'localizedValue': item.get('localizedValue')
                }
        return characteristics

    def extract_property_data(self, ad_data, link):
        characteristics = self.get_characteristics_dict(ad_data)
        
        # Lokalizacja
        location = self.safe_get(ad_data, ['location'], {})
        address = self.safe_get(location, ['address'], {})
        coordinates = self.safe_get(location, ['coordinates'], {})

        # Zdjęcia
        images = self.safe_get(ad_data, ['images'], [])
        photo_urls = [img.get('large', '') for img in images if img.get('large')]

        # Piętro
        floor = " / ".join(filter(None, [
            self.safe_get(characteristics, ['floor_no', 'localizedValue']),
            self.safe_get(characteristics, ['building_floors_num', 'localizedValue'])
        ]))
        floor = f"P: {floor}" if floor else "Brak danych"

        property_data = {
            "Tytuł": self.safe_get(ad_data, ['title'], "Brak tytułu"),
            "Cena (PLN)": self.safe_get(characteristics, ['price', 'value'], 0),
            "Cena za m² (PLN)": self.safe_get(characteristics, ['price_per_m', 'value'], 0),
            "Lokalizacja": ", ".join(filter(None, [
                self.safe_get(address, ['street', 'name']),
                self.safe_get(address, ['district', 'name']),
                self.safe_get(address, ['city', 'name'])
            ])),
            "Szerokość geo": self.safe_get(coordinates, ['latitude'], "Brak danych"),
            "Długość geo": self.safe_get(coordinates, ['longitude'], "Brak danych"),
            "Metraż (m²)": self.safe_get(characteristics, ['m', 'value'], 0),
            "Piętro": floor,
            "Liczba pokoi": self.safe_get(characteristics, ['rooms_num', 'value'], 0),
            "Rynek": self.safe_get(characteristics, ['market', 'localizedValue'], "Brak danych"),
            "Stan wykończenia": self.safe_get(characteristics, ['construction_status', 'localizedValue'], "Brak danych"),
            "Rok budowy": self.safe_get(characteristics, ['build_year', 'value'], "Brak danych"),
            "Materiał budynku": self.safe_get(characteristics, ['building_material', 'localizedValue'], "Brak danych"),
            "Okna": self.safe_get(characteristics, ['windows_type', 'localizedValue'], "Brak danych"),
            "Ogrzewanie": self.safe_get(characteristics, ['heating', 'localizedValue'], "Brak danych"),
            "Winda": "Tak" if 'winda' in self.safe_get(ad_data, ['features'], []) else "Nie",
            "Czynsz (PLN)": self.safe_get(characteristics, ['rent', 'value'], 0),
            "Typ ogłoszeniodawcy": self.safe_get(characteristics, ['advertiser_type', 'localizedValue'], "Brak danych"),
            "Certyfikat energetyczny": self.safe_get(characteristics, ['energy_certificate', 'localizedValue'], "Brak danych"),
            "Liczba zdjęć": len(images),
            "Zdjęcia": " | ".join(photo_urls) if photo_urls else "Brak zdjęć",
            "Data utworzenia": self.safe_get(ad_data, ['createdAt'], "").split("T")[0],
            "Data modyfikacji": self.safe_get(ad_data, ['modifiedAt'], "").split("T")[0],
            "Opis": self.safe_get(ad_data, ['description'], "Brak opisu").replace("\n", " ").strip(),
            "Link": link,
            "Dodatkowe informacje": " | ".join(self.safe_get(ad_data, ['features'], []))
        }

        # Konwersja pól numerycznych
        numeric_fields = ['Cena (PLN)', 'Cena za m² (PLN)', 'Metraż (m²)', 'Liczba pokoi', 'Czynsz (PLN)']
        for field in numeric_fields:
            try:
                property_data[field] = float(property_data[field])
            except:
                property_data[field] = 0.0

        return property_data

    def process_property(self, link):
        try:
            response = self.session.get(link, timeout=10)
            response.raise_for_status()
        except Exception as e:
            print(f"Błąd pobierania: {link} - {str(e)[:100]}")
            return None

        try:
            soup = BeautifulSoup(response.text, "html.parser")
            script_tag = soup.find('script', id='__NEXT_DATA__')
            if not script_tag:
                return None

            data = json.loads(script_tag.string)
            ad_data = self.safe_get(data, ['props', 'pageProps', 'ad'], {})
            return self.extract_property_data(ad_data, link) if ad_data else None

        except Exception as e:
            print(f"Błąd przetwarzania: {link} - {str(e)[:100]}")
            return None

    def get_property_links(self, page):
        url = f"https://www.otodom.pl/pl/wyniki/sprzedaz/mieszkanie/cala-polska?page={page}"
        try:
            response = self.session.get(url, timeout=15)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, "html.parser")
            
            links = []
            for listing in soup.find_all("article", {"data-cy": "listing-item"}):
                link_tag = listing.find("a", {"data-cy": "listing-item-link"})
                if link_tag and link_tag.get("href"):
                    full_link = urljoin("https://www.otodom.pl", link_tag["href"])
                    links.append(full_link)
            
            time.sleep(random.uniform(0.7, 1.5))
            return links

        except Exception as e:
            print(f"Błąd strony {page}: {str(e)[:100]}")
            return []

    def scrape(self, start_page=1, end_page=1, max_workers=4, page_workers=5):
        all_links = []
        print("\n[ETAP 1] Zbieranie linków do ofert...")
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=page_workers) as executor:
            future_to_page = {
                executor.submit(self.get_property_links, page): page 
                for page in range(start_page, end_page + 1)
            }
            
            for future in concurrent.futures.as_completed(future_to_page):
                page = future_to_page[future]
                try:
                    links = future.result()
                    all_links.extend(links)
                    print(f" Strona {page}/{end_page} - zebrano {len(links)} linków", end="\r")
                except Exception as e:
                    print(f"Błąd strony {page}: {str(e)[:100]}")

        print(f"\nZnaleziono {len(all_links)} ofert")

        print("\n[ETAP 2] Pobieranie szczegółów...")
        properties = []
        with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = {executor.submit(self.process_property, link): link for link in all_links}
            for i, future in enumerate(concurrent.futures.as_completed(futures), 1):
                result = future.result()
                if result:
                    properties.append(result)
                print(f" Postęp: {i}/{len(all_links)} ({len(properties)} udanych)", end="\r")

        self.save_to_csv(properties)
        return properties

    def save_to_csv(self, data):
        if not data:
            print("\nBrak danych do zapisania")
            return

        filename = f"otodom_mieszkania_{time.strftime('%Y%m%d-%H%M')}.csv"
        fieldnames = [
            'Tytuł', 'Cena (PLN)', 'Cena za m² (PLN)', 'Lokalizacja',
            'Szerokość geo', 'Długość geo', 'Metraż (m²)', 'Piętro',
            'Liczba pokoi', 'Rynek', 'Stan wykończenia', 'Rok budowy',
            'Materiał budynku', 'Okna', 'Ogrzewanie', 'Winda', 'Czynsz (PLN)',
            'Typ ogłoszeniodawcy', 'Certyfikat energetyczny', 'Liczba zdjęć',
            'Zdjęcia', 'Data utworzenia', 'Data modyfikacji', 'Opis', 'Link',
            'Dodatkowe informacje'
        ]

        with open(filename, 'w', newline='', encoding='utf-8-sig') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(data)

        print(f"\nDane zapisano do: {filename}")
        print(f"Liczba zebranych ofert: {len(data)}")


if __name__ == "__main__":
    scraper = OtodomScraper()
    
    # Konfiguracja
    START_PAGE = 1
    END_PAGE = 5110  # Przetestuj z mniejszą liczbą stron przed pełnym scrapowaniem
    PAGE_WORKERS = 5  # Wątki do zbierania linków
    DETAIL_WORKERS = 3  # Wątki do szczegółów
    
    print(f"Rozpoczynanie scrapowania (strony {START_PAGE}-{END_PAGE})...")
    scraper.scrape(
        start_page=START_PAGE,
        end_page=END_PAGE,
        page_workers=PAGE_WORKERS,
        max_workers=DETAIL_WORKERS
    )
