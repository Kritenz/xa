import os
import time

import requests
from selenium import webdriver
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

URL_EVENTO = 'https://www.movistararena.com.ar/show/949f1877-625b-479f-893a-1ae09da0f00f'
SELECTOR_FILA = "div.evento-row"

# True = te avisa SIEMPRE con el resumen de todas las fechas (para probar).
# False = solo avisa cuando hay entradas disponibles.
MODO_PRUEBA = True

# Fechas que NO querés que disparen aviso (formato "día mes", en minúsculas).
FECHAS_IGNORAR = ["06 febrero"]

# Si querés avisos solo de ciertas fechas, completá la lista. Vacía = cualquiera.
FECHAS_INTERES = []   # ejemplo: ["13 noviembre", "14 noviembre"]


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
            continue  # Blazor re-renderizó la fila mientras la leíamos
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
            if f["clave"] in FECHAS_IGNORAR:
                continue
            if FECHAS_INTERES and f["clave"] not in FECHAS_INTERES:
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
        elif MODO_PRUEBA:
            avisar_telegram(
                f"🧪 Prueba: {estado}\n" + resumen_completo(funciones)
            )
    finally:
        driver.quit()


if __name__ == "__main__":
    main()
