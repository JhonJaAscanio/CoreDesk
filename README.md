# CoreDesk

Navegador de escritorio para Windows con pestañas, basado en PyQt6 y Qt WebEngine (Chromium 140).

## Funciones

- Pestañas: abrir (`Ctrl+T`), cerrar (`Ctrl+W`), reordenar, duplicar y reabrir la última cerrada (`Ctrl+Mayús+T`).
- Barra de direcciones con indicador de conexión segura y sugerencias del historial.
- Página de inicio propia, búsqueda en la página (`Ctrl+F`), zoom y pantalla completa (`F11`).
- Descargas con selección de destino y menú de descargas recientes.
- Guardar página como PDF (`Ctrl+P`).
- Restauración de las pestañas de la sesión anterior.
- Avisos para permisos web (cámara, micrófono, notificaciones, ubicación), certificados no válidos,
  autenticación HTTP/proxy y certificados de cliente.
- Recuperación de pestañas cuyo proceso se cierra inesperadamente.
- Borrado de datos de navegación (`Ctrl+Mayús+Supr`) y registro de errores.

## Requisitos

- Windows 10/11
- Python 3.11

```bash
py -3.11 -m pip install -r requirements.txt
```

## Ejecutar

```bash
py -3.11 CoreDesk.py
```

## Compilar el ejecutable

```bash
py -3.11 -m PyInstaller --noconfirm --clean CoreDesk.spec
```

El resultado queda en `dist/CoreDesk/`. Se distribuye la carpeta completa: `CoreDesk.exe` necesita la
carpeta `_internal` que está a su lado. Se usa el formato de carpeta porque el de un solo archivo
descomprime Qt WebEngine en cada arranque y tarda unas cuatro veces más en abrir.

## Versión anterior (Autorizador)

La primera vez que se abre, CoreDesk copia las sesiones iniciadas, el historial y las pestañas de una
instalación anterior de Autorizador. Los datos originales no se modifican ni se borran. Si Autorizador o una
versión anterior de CoreDesk está abierta, sus archivos están bloqueados: CoreDesk lo avisa, no deja copias a
medias y vuelve a intentarlo en el siguiente arranque.

Si se ejecuta con el Python de la Microsoft Store, Windows guarda los datos en una carpeta propia de ese
Python, por lo que el ejecutable y el script no comparten sesiones.

## Pruebas

```bash
py -3.11 -m unittest discover -s tests -v
```

## Icono

`icon.ico` se genera con:

```bash
py -3.11 tools/make_icon.py icon.ico icon_preview.png
```
