import os
import time

import requests
from selenium import webdriver
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

URL_EVENTO = 'https://www.movistararena.com.ar/show/949f1877-625b-479f-893a-1ae09da0f00f'
SELECTOR_BOTON = "span.mud-button-label"


def avisar_telegram(mensaje):
    requests.post(
        f"https://api.telegram.org/bot{os.environ['TELEGRAM_TOKEN']}/sendMessage",
        data={"chat_id": os.environ["TELEGRAM_CHAT_ID"], "text": mensaje},
        timeout=10,
    )


def leer_botones(driver):
    """Devuelve los textos de todos los botones MudBlazor visibles."""
    textos = []
    for el in driver.find_elements(By.CSS_SELECTOR, SELECTOR_BOTON):
        try:
            if el.is_displayed():
                textos.append(el.text.strip().lower())
        except Exception:
            continue  # Blazor re-renderizó el elemento mientras lo leíamos
    return textos


def revisar_pagina(driver):
    try:
        driver.get(URL_EVENTO)

        # Espera a que Blazor renderice al menos un botón
        WebDriverWait(driver, 30).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, SELECTOR_BOTON))
        )
        time.sleep(1.5)  # margen por si el texto cambia tras el primer render

        botones = leer_botones(driver)
        print(f"Botones encontrados: {botones}")

        if any("comprar" in b for b in botones):
            return True
        if any("agotado" in b for b in botones):
            print("Sigue AGOTADO.")
        else:
            print("Estado desconocido.")

    except Exception as e:
        print(f"Ocurrió un error: {e}")

    return False


def main():
    options = Options()
    options.add_argument("-headless")  # obligatorio en un servidor
    driver = webdriver.Firefox(options=options)
    try:
        if revisar_pagina(driver):
            avisar_telegram(f"🚨 ¡HAY BOTÓN COMPRAR! {URL_EVENTO}")
            print("Aviso enviado por Telegram.")
    finally:
        driver.quit()


if __name__ == "__main__":
    main()
