# Circuito completamente cableado de MyHealthKit

Entrega principal:

- `images/design/circuit_design.wired.png`: imagen para el README.
- `images/design/circuit_design.wired.svg`: exportación vectorial de Fritzing.
- `hardware/fritzing/MyHealthKit.fzz`: proyecto editable autocontenido; abrir **Breadboard / Protoboard**.

## Cambios de esta versión

Se han eliminado las dos protoboards. Todas las conexiones externas se representan con cables continuos y uniones reales entre terminales; no se usan etiquetas de red para sustituir tramos de cable. Los puntos representan empalmes eléctricos. Dos cables que se cruzan sin punto no están conectados.

Se han distribuido los motores y drivers a la izquierda, la Raspberry Pi en el centro, los servos y el RPLidar a la derecha y las fuentes de alimentación abajo. Los recorridos son horizontales o verticales. Se compararon varias distribuciones y prioridades de recorrido para reducir los cruces. Los cruces restantes son a 90 grados. Los cables evitan los cuerpos de otras piezas; los pequeños tramos de salida de los contactos GPIO pasan por el área del propio conector, como corresponde al acceso a sus pines.

La figura contiene 13 módulos dibujados: Raspberry Pi 4, dos TB6612FNG, cuatro N20, dos servos MG996R, batería de litio, convertidor DC–DC, portapilas de cuatro AAA y un símbolo del RPLidar C1 con su adaptador USB.

## RPLidar C1

No se localizó una pieza pública específica para el C1 en las búsquedas realizadas. Se añadió una pieza sencilla de documentación en Fritzing: scanner C1 más el adaptador USB/UART de su kit. No es una huella de PCB ni representa las dimensiones del equipo.

El adaptador se conecta a un puerto USB de la Raspberry Pi mediante cuatro conductores: 5 V, GND, D+ y D−. La alimentación y el retorno USB se conectan internamente al dominio de alimentación de la Raspberry Pi. Los pines UART del sensor quedan dentro del módulo que agrupa C1 y adaptador; no se conectan a los GPIO utilizados por los servos.

Esta interfaz coincide con el [manual de SLAMTEC para el kit C1](https://openzeka.com/wp-content/uploads/2024/02/SLAMTEC_rplidarkit_usermanual_C1_v1.0_en.pdf), apartados de conexión y cable USB, y con la configuración `/dev/ttyUSB0` a 460800 baudios de `myhealthkit.launch`. [Producto C1 de SLAMTEC](https://www.slamtec.com/en/c1).

## Conexiones de control

Se conserva la asignación del circuito reconstruido anterior, coincidente con `MyHealthController/SLAM/catkin_ws/src/my_slam_setup/config/motors.yaml` y el controlador ROS:

| Señal | Driver 1 | Driver 2 |
|---|---|---|
| AIN1 | GPIO18 | GPIO22 |
| AIN2 | GPIO27 | GPIO23 |
| BIN1 | GPIO24 | GPIO5 |
| BIN2 | GPIO25 | GPIO6 |
| STBY | GPIO21 | GPIO21 |
| PWMA y PWMB | 3V3 | 3V3 |

Los cuatro motores tienen sus dos terminales cableados a los pares de salida de los drivers. La compuerta usa GPIO15 y la ruleta GPIO14, según los scripts de los servos. La numeración GPIO es BCM.

La batería de litio alimenta el convertidor. Su salida de 5 V alimenta la Raspberry Pi y ambos servos. El portapilas alimenta VM de ambos drivers. La lógica VCC y los PWM de los drivers reciben 3V3. Todos los retornos GND están conectados físicamente; los empalmes sustituyen las barras de las protoboards retiradas.

## Comprobaciones

El FZZ se ha cargado y exportado con Fritzing CD548. La imagen PNG se ha obtenido rasterizando ese SVG, sin redibujar sus componentes.

La comprobación independiente del grafo guardado en el FZZ confirma que todos los terminales utilizados pertenecen a su red esperada, que no hay extremos de cable abiertos y que no hay cortocircuitos entre redes distintas. También se comprueban los tramos ortogonales, la ausencia de solapamientos paralelos entre redes y la ausencia de uniones en T accidentales. El resultado se conserva en `hardware/circuit-validation.json`.

La pieza de anotaciones solo contiene textos y marcas de uniones; no contiene buses que sustituyan cables. La única representación interna añadida a la Raspberry Pi es su interfaz USB de alimentación y datos.

## Piezas y procedencia

- [Raspberry Pi 4B de la comunidad Fritzing](https://forum.fritzing.org/t/raspberry-pi-4-model-b/8622); se añadió la interfaz USB al símbolo para conectar el C1.
- [N20 / DC Mini Metal Gear Motor](https://forum.fritzing.org/t/anyone-got-an-n20-geared-mini-motor-fritzing-part/10380).
- [Multi Booster de BlueAG](https://github.com/BlueAG/Fritzing-Parts), pieza 288.
- [Biblioteca Fritzing](https://github.com/fritzing/fritzing-parts): TB6612FNG, símbolo de servo, batería y portapilas. Las ilustraciones genéricas de servo y batería identifican el tipo de componente; sus rótulos de biblioteca no sustituyen las especificaciones del montaje.
- RPLidar C1: símbolo sencillo creado para esta figura a petición del usuario, con interfaz basada en el manual de SLAMTEC.
- [Pololu: TB6612FNG y su esquema](https://www.pololu.com/product/713).

El PNG original permanece en `images/design/circuit_design.png`. La reconstrucción utiliza los componentes confirmados y la asignación del código; no certifica cada conexión histórica del PNG antiguo, que contenía omisiones. Las verificaciones descritas se refieren al archivo y a su conectividad, no a una prueba física del robot.
