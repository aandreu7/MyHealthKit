# Servidor y dispensador

Las rutas y los campos de respuesta usados por MyHealthCall se conservan. No se ha
añadido autenticación ni cambiado la exposición HTTP de la API.
El cliente de altas ahora comprueba el estado HTTP: un error del servidor o el
inventario lleno ya no se presentan en la app como un alta exitosa.

## Instalación y arranque

Desde `MyHealthController`, en el entorno Python que ejecutará el servidor:

```bash
python3 -m pip install -r requirements.txt
sudo apt-get install ffmpeg
python3 database/creation_script.py
python3 server/app.py
```

También se puede iniciar con `python3 -m MyHealthController.server.app` desde la
raíz del proyecto, o importar `server.app:app` desde un servidor WSGI situado en
`MyHealthController`. Si se usa navegación, cargar antes el entorno catkin de la
misma instalación; el proceso hijo usa el mismo intérprete Python del servidor.

El script de creación inicializa una base vacía o migra la existente. Ya no inserta
medicamentos ficticios. La migración conserva registros e IDs e incorpora posición
única y rango 0–7. Si encuentra posiciones repetidas o inválidas, se detiene para
que se reconcilien con el robot; no elimina registros automáticamente.

Los recursos se buscan respecto a la instalación, independientemente del directorio
de trabajo:

- Base de datos: `MyHealthController/database/pharmacy.db`.
- Claves: `MyHealthController/server/keys.env`.
- Modelos: `MyHealthController/server/vosk-models/`.
- Audios: `MyHealthController/data/audio/`.
- Última orden del servo: `IO_controllers/servomotors/current_position.txt`.

Se pueden configurar `MYHEALTHKIT_DATABASE`, `MYHEALTHKIT_KEYS`,
`MYHEALTHKIT_MODELS`, `MYHEALTHKIT_DATA_DIR` y `MYHEALTHKIT_SERVO_STATE` como
variables de entorno. Las rutas relativas se interpretan desde `MyHealthController`.
El usuario del proceso necesita permiso de escritura en la base de datos, sus
archivos de bloqueo, el directorio de audios y el archivo de estado del servo.
Todos los workers deben compartir las mismas rutas y un sistema de archivos local.

## IA y voz

El inventario y la navegación no requieren claves ni modelos de IA. Para OCR e IA,
configurar `OCR_API_KEY`, `OPENROUTER_API_KEY` y, opcionalmente, `TOGETHER_API_KEY`.
`OPENROUTER_MODELS` permite indicar una lista separada por comas y `TOGETHER_MODEL`
el modelo alternativo. Se conservan los modelos de ejemplo del proyecto: su
disponibilidad depende del proveedor; no se ha verificado mediante peticiones reales.

Para transcribir audio hacen falta ffmpeg en PATH y uno de estos modelos de Vosk:
`vosk-model-en-us-0.22-lgraph` o `vosk-model-es-0.42`. Elegir el idioma mediante
`MYHEALTHKIT_LANGUAGE=en-US` o `es-ES`. Puede configurarse `FFMPEG_BINARY`.
Los modelos se cargan al necesitarlos y se reutilizan; cada transcripción usa un
reconocedor propio.

Las imágenes se guardan en directorios temporales privados y se eliminan incluso
si falla el OCR o la IA. El audio de entrada se entrega por una tubería a ffmpeg.
Cada respuesta de voz tiene una URL distinta, devuelta en `audioUri`. Los audios
caducan después de una hora y se limpian al generar otros diagnósticos. No existe
un audio global de la última petición. La reproducción en el robot se serializa;
`MYHEALTHKIT_PLAY_AUDIO=0` la desactiva. Si falla el altavoz, sigue disponible el
audio de la respuesta para el teléfono.

Se validan los campos obligatorios y sus tipos. Una lista vacía de recomendaciones
es válida, y se rechazan recomendaciones que no estén en el inventario. Esto valida
el formato y la pertenencia al inventario; no certifica el contenido clínico generado.

## Operaciones del dispensador

Las altas, retiradas y borrados se serializan con bloqueos entre procesos y una
transacción SQLite. Al llenar los ocho compartimentos se devuelve HTTP 409 sin
mover el servo. Nunca se reserva un noveno hueco. El movimiento completo se ejecuta
en un proceso que mantiene un bloqueo compartido por las herramientas de servo:

1. Cerrar trampilla.
2. Girar hasta el compartimento.
3. Si se retira/borrar, abrir y esperar dos segundos.
4. Intentar cerrar siempre, también si falla el giro o la apertura.

Una selección conserva el medicamento para su devolución manual, como en el
funcionamiento original. Un borrado lo retira físicamente y solo elimina el registro
tras terminar la secuencia. Un alta posiciona la ruleta con la puerta cerrada para
la colocación manual. El estado del archivo del servo registra la última orden,
no una posición medida, y no es necesario para mandar una posición absoluta.
Los scripts limpian exclusivamente los GPIO que han utilizado.

Los errores de hardware revierten la transacción. Un corte eléctrico puede ocurrir
entre el movimiento físico y el commit: sin sensores no se puede hacer atómica la
realidad física con SQLite ni confirmar la colocación/caída del medicamento.
Tras un corte o fallo mecánico, comprobar el compartimento antes de repetir la orden.
No utilizar scripts de prueba de motores mientras está activo ROS.

## Pruebas

Desde la raíz del proyecto:

```bash
python3 -m unittest discover -s MyHealthController/server/tests -v
python3 -m unittest discover -s MyHealthController/SLAM/catkin_ws/src/my_slam_setup/tests -v
```

Se usa Flask, SQLite y bloqueos reales. Los servos, OCR, modelos y TTS se simulan;
quedan pendientes las comprobaciones físicas y las llamadas reales a los proveedores.
