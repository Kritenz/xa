import os
import time

import requests
from selenium import webdriver
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

URL_EVENTO = 'https://www.movistararena.com.ar/show/993a2d46-39d7-4455-b199-87a5a2dc9b83'
SELECTOR_BOTON = "span.mud-button-label"

# True = te avisa SIEMPRE (para probar). False = solo avisa cuando hay "comprar".
MODO_PRUEBA = True


def avisar_telegram(mensaje):
    try:
        r = requests.post(
            f"https://api.telegram.org/bot{os.environ['TELEGRAM_TOKEN']}/sendMessage",
            data={"chat_id": os.environ["TELEGRAM_CHAT_ID"], "text": mensaje},
            timeout=10,
        )
        print(f"Respuesta de Telegram: {r.status_code} {r.text}")
    except Exception as e:
        print(f"Error al enviar a Telegram: {e}")


def leer_botones(driver):
    """Devuelve los textos de todos los botones MudBlazor visibles."""
    textos = []
    for el in driver.find_elements(By.CSS_SELECTOR, SELECTOR_BOTON):
        try:
            if el.is_displayed():
                textos.append(el.text.strip().lower())
        except Exception:
            continue
    return textos


def revisar_pagina(driver):
    """Devuelve: 'comprar', 'agotado', 'desconocido' o 'error'."""
    try:
        driver.get(URL_EVENTO)

        WebDriverWait(driver, 30).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, SELECTOR_BOTON))
        )
        time.sleep(1.5)

        botones = leer_botones(driver)
        print(f"Botones encontrados: {botones}")

        if any("comprar" in b for b in botones):
            return "comprar"
        if any("agotado" in b for b in botones):
            print("Sigue AGOTADO.")
            return "agotado"
        print("Estado desconocido.")
        return "desconocido"

    except Exception as e:
        print(f"Ocurrió un error: {e}")
        return "error"


def main():
    options = Options()
    options.add_argument("-headless")
    driver = webdriver.Firefox(options=options)
    try:
        estado = revisar_pagina(driver)
        print(f"Estado final: {estado}")

        if estado == "comprar":
            avisar_telegram(f"🚨 ¡HAY BOTÓN COMPRAR! {URL_EVENTO}")
        elif MODO_PRUEBA:
            avisar_telegram(f"🧪 Prueba: estado = {estado}")
    finally:
        driver.quit()


if __name__ == "__main__":
    main()
