import os
import sys
import time
import json
import subprocess
import urllib.request
import urllib.error


AIVEN_API = "https://api.aiven.io/v1"

TOKEN = os.environ.get("AIVEN_TOKEN")
PROJECT = os.environ.get("AIVEN_PROJECT")
SERVICE = os.environ.get("AIVEN_SERVICE")


def log(message):
    print(f"[AIVEN STARTUP] {message}", flush=True)


def api_request(url, method="GET", data=None):
    headers = {
        "Authorization": f"aivenv1 {TOKEN}",
        "Content-Type": "application/json",
    }

    body = None

    if data is not None:
        body = json.dumps(data).encode("utf-8")

    request = urllib.request.Request(
        url,
        data=body,
        headers=headers,
        method=method,
    )

    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            content = response.read()

            if not content:
                return {}

            return json.loads(content.decode("utf-8"))

    except urllib.error.HTTPError as error:
        body = error.read().decode("utf-8", errors="replace")

        log(f"Error HTTP {error.code} comunicándose con Aiven.")
        log(body)

        raise


def get_service():
    url = (
        f"{AIVEN_API}/project/{PROJECT}"
        f"/service/{SERVICE}"
    )

    return api_request(url)


def power_on_service():
    url = (
        f"{AIVEN_API}/project/{PROJECT}"
        f"/service/{SERVICE}"
    )

    log("Solicitando encendido de PostgreSQL...")

    return api_request(
        url,
        method="PUT",
        data={
            "powered": True
        },
    )


def wait_for_aiven():
    log("Comprobando estado de PostgreSQL en Aiven...")

    service_data = get_service()

    service = service_data.get("service", service_data)

    state = str(
        service.get("state", "")
    ).upper()

    powered = service.get("powered")

    log(
        f"Estado informado por Aiven: "
        f"state={state or 'desconocido'}, powered={powered}"
    )

    if powered is False:
        power_on_service()

    elif state in {"POWEROFF", "POWEREDOFF", "POWERED_OFF"}:
        power_on_service()

    else:
        log("El servicio no aparece apagado. Esperando disponibilidad.")

    # Aiven puede tardar varios minutos en restaurar
    # PostgreSQL después de un Power On.
    max_wait_seconds = 15 * 60
    interval_seconds = 15
    elapsed = 0

    while elapsed < max_wait_seconds:

        try:
            service_data = get_service()
            service = service_data.get("service", service_data)

            state = str(
                service.get("state", "")
            ).upper()

            log(f"Estado actual: {state or 'desconocido'}")

            if state == "RUNNING":
                log("PostgreSQL está listo.")
                return

        except Exception as error:
            log(f"Aiven todavía no está disponible: {error}")

        time.sleep(interval_seconds)
        elapsed += interval_seconds

    raise TimeoutError(
        "Aiven no estuvo disponible después de 15 minutos."
    )


def start_gunicorn():
    log("Iniciando Gunicorn...")

    os.execvp(
        "gunicorn",
        [
            "gunicorn",
            "config.wsgi:application",
            "--bind",
            "0.0.0.0:" + os.environ.get("PORT", "10000"),
        ],
    )


def main():

    missing = []

    if not TOKEN:
        missing.append("AIVEN_TOKEN")

    if not PROJECT:
        missing.append("AIVEN_PROJECT")

    if not SERVICE:
        missing.append("AIVEN_SERVICE")

    if missing:
        log(
            "Faltan variables de entorno: "
            + ", ".join(missing)
        )
        sys.exit(1)

    try:
        wait_for_aiven()
        start_gunicorn()

    except Exception as error:
        log(f"ERROR DE ARRANQUE: {error}")
        sys.exit(1)


if __name__ == "__main__":
    main()