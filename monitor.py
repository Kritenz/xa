import os
import time

import requests
from selenium import webdriver
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

URL_EVENTO = 'https://www.movistararena.com.ar/show/993a2d46-39d7-4455-b199-87a5a2dc9b83'
SELECTOR_FILA = "div.evento-row"

MODO_PRUEBA = False


def avisar_telegram(mensaje):
    """Envía el mensaje a Telegram una sola vez de forma limpia."""
    url = f"https://api.telegram.org/bot{os.environ['TELEGRAM_TOKEN']}/sendMessage"
    payload = {"chat_id": os.environ["TELEGRAM_CHAT_ID"], "text": mensaje}
    
    try:
        r = requests.post(url, data=payload, timeout=15)
        print(f"Respuesta de Telegram: {r.status_code} {r.text}")
    except Exception as e:
        print(f"Error al enviar a Telegram: {e}")


def leer_funciones(driver):
    """Lee cada fila del evento y devuelve una lista de diccionarios."""
    funciones = []
    for fila in driver.find_elements(By.CSS_SELECTOR, SELECTOR_FILA):
        try:
            dia = fila.find_element(By.CSS_SELECTOR, ".fecha p").text.strip()
            mes = fila.find_element(By.CSS_SELECTOR, ".fecha span").text.strip()

            horarios = []
            for hora in fila.find_elements(By.CSS_SELECTOR, ".hora"):
                h = hora.find_element(By.CSS_SELECTOR, "p").text.strip()
                tipo = hora.find_element(By.CSS_SELECTOR, "span").text.strip()
                horarios.append(f"{tipo} {h}")

            boton = fila.find_element(By.CSS_SELECTOR, "button .mud-button-label")
            estado = boton.text.strip().lower()

            funciones.append({
                "clave": f"{dia} {mes}".lower(),
                "fecha": f"{dia} de {mes}",
                "horarios": " / ".join(horarios),
                "estado": estado,
            })
        except Exception:
            continue
    return funciones


def revisar_pagina(driver):
    """Devuelve (estado, funciones, para_avisar)."""
    try:
        driver.get(URL_EVENTO)
        WebDriverWait(driver, 30).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, SELECTOR_FILA))
        )
        time.sleep(1.5)

        funciones = leer_funciones(driver)
        for f in funciones:
            print(f"{f['fecha']} | {f['horarios']} | {f['estado']}")

        if not funciones:
            return "desconocido", [], []

        para_avisar = []
        for f in funciones:
            if "comprar" not in f["estado"]:
                continue
            para_avisar.append(f)

        if para_avisar:
            return "comprar", funciones, para_avisar
        return "sin novedades", funciones, []

    except Exception as e:
        print(f"Ocurrió un error: {e}")
        return "error", [], []


def resumen_completo(funciones):
    """Lista de todas las fechas: 🟢 con entradas, 🔴 agotadas."""
    lineas = []
    for f in funciones:
        icono = "🟢" if "comprar" in f["estado"] else "🔴"
        lineas.append(f"{icono} {f['fecha']}: {f['estado']}")
    return "\n".join(lineas) or "(no se leyó ninguna fecha)"


def main():
    options = Options()
    options.add_argument("-headless")
    
    driver = webdriver.Firefox(options=options)
    try:
        estado, funciones, para_avisar = revisar_pagina(driver)
        print(f"Estado final: {estado}")

        if estado == "comprar":
            nuevas = [f"📅 {f['fecha']} ({f['horarios']})" for f in para_avisar]
            avisar_telegram(
                "🚨 ¡HAY ENTRADAS!\n"
                + "\n".join(nuevas)
                + "\n\nEstado de todas las fechas:\n"
                + resumen_completo(funciones)
                + f"\n\n{URL_EVENTO}"
            )
        else:
            print("No hay entradas disponibles. No se envía mensaje.")
            
    finally:
        driver.quit()


if __name__ == "__main__":
    main()
