# Navegación con RPLidar, sin encoders ni IMU

Esta revisión usa ROS 1 Noetic y Hector SLAM. No inventa movimiento a partir de
`cmd_vel`: estima la pose mediante scan matching y deriva de ella la velocidad.
No necesita encoders, IMU, AMCL ni robot_localization. La velocidad derivada es
ruidosa y se filtra; no es una medición independiente del LiDAR.

## Arquitectura

```text
RPLidar -- /scan --> Hector -- /slam_out_pose --> lidar_odometry
                         \-- /map                     |-- /odom (pose + twist)
                                                      |-- TF odom -> base_link
                                                      \-- /navigation/healthy
destino -- move_base action --> Navfn + DWA -- /cmd_vel --> motor_controller
```

El árbol TF tiene un único publicador por arista:

```text
map -- identidad estática --> odom -- pose LiDAR --> base_link -- montaje --> laser
```

`map` y `odom` coinciden durante esta sesión: no existe una fuente independiente
para separar deriva local y correcciones globales. Hector tiene desactivadas sus
publicaciones TF y su odometría nativa (esta última no calcula `twist`). No se usa
la pose derivada como entrada de Hector; se evita un bucle de realimentación.
La transformación dinámica conserva el timestamp del scan, sin extrapolarla.

El costmap global incluye el mapa de Hector, obstáculos recientes e inflación.
El local es una ventana móvil con obstáculos e inflación. Navfn no planifica por
celdas desconocidas: primero hay que explorar el trayecto de manera supervisada.
DWA se configura para tracción diferencial, sin desplazamiento lateral, a un
máximo inicial de 0.15 m/s y 0.4 rad/s. No hay recuperaciones automáticas de giro.

## Instalar en la Raspberry

Usar un entorno Linux con ROS Noetic y Python 3.8. No copiar los directorios
`build`, `devel` ni los entornos `env` del repositorio: deben regenerarse en la Pi.
Desde `MyHealthController/SLAM/catkin_ws`:

```bash
source /opt/ros/noetic/setup.bash
sudo apt-get install ros-noetic-hector-slam ros-noetic-navigation \
  python3-rosdep python3-yaml python3-gpiozero python3-rpi.gpio python3-nose
# El driver debe ser la versión de Slamtec con soporte para el RPLidar C1.
# Si ya existe en src, actualizar/verificar esa copia en vez de duplicarlo.
git clone --recurse-submodules https://github.com/Slamtec/rplidar_ros.git src/rplidar_ros
rosdep install --from-paths src --ignore-src -r -y
catkin_init_workspace src
catkin_make
source devel/setup.bash
catkin_make run_tests_my_slam_setup
catkin_test_results
```

Inicializar rosdep antes si el equipo nunca lo ha usado (`sudo rosdep init` y
`rosdep update`). No ejecutar `catkin_init_workspace` si ya hay un `src/CMakeLists.txt`
válido de catkin; si contiene únicamente la ruta textual a `/opt/ros/...`,
reemplazar ese archivo por el generado por catkin en Linux.
Registrar la revisión del driver instalada con `git -C src/rplidar_ros rev-parse HEAD`.

El usuario que ejecuta los nodos necesita acceso al puerto serie y a GPIO
(habitualmente grupos `dialout` y `gpio`, dependiendo de la distribución).

## Arranque y calibración

Primero arrancar sin motores:

```bash
roslaunch my_slam_setup myhealthkit.launch serial_port:=/dev/ttyUSB0 \
  laser_x:=0.0 laser_y:=0.0 laser_z:=0.0 laser_yaw:=0.0
```

Los offsets son ejemplos: medir la posición del LiDAR respecto al centro de giro
y su orientación (yaw en radianes). No dejar el montaje a cero si no corresponde.
Baudios por defecto: 460800, modo Standard y frecuencia solicitada de 10 Hz,
siguiendo el launch oficial del C1.

En RViz fijar `Fixed Frame: map` y añadir `/scan`, `/map`, TF y los costmaps.
Mover el robot lentamente a mano: el mapa debe permanecer coherente y el robot
debe desplazarse en él. Revisar:

```bash
rostopic hz /scan
rostopic hz /slam_out_pose
rostopic echo /navigation/healthy
rostopic echo /odom
rosrun tf tf_echo map base_link
rostopic info /odom
rostopic info /cmd_vel
```

En reposo, el twist debe ser aproximadamente cero. Al avanzar, `linear.x` debe ser
positivo; al girar a la izquierda, `angular.z` debe ser positivo. Debe existir un
único publicador de `/odom` y un único controlador de GPIO.

Antes de habilitar motores, ajustar `config/motors.yaml`:

- Pines BCM y `motor_signs` (izquierda delantera/trasera, derecha delantera/trasera).
- `wheel_base`: distancia efectiva entre los lados; calibrar también el giro.
- `speed_at_full_duty`: velocidad lineal medida con esa alimentación. La conversión
  a PWM es de lazo abierto y aproximada; DWA realimenta con la velocidad LiDAR.
- Comprobar que PWMA/PWMB de ambos TB6612 están a HIGH: este driver aplica PWM a
  IN1/IN2. Si se cablean PWM dedicados, habrá que adaptar el driver.
- Medir la envolvente completa del robot y ajustar `robot_radius` o un `footprint`
  poligonal. El radio 0.20 m es provisional, no una medida certificada.

Con las ruedas levantadas, comprobar primero los sentidos. Después, a baja velocidad
y en una zona despejada, medir avance y giro usando el LiDAR o distancia/tiempo.
Reiniciar el launch para cargar cambios de parámetros:

```bash
roslaunch my_slam_setup myhealthkit.launch enable_motors:=true
```

El antiguo `IO_controllers/dc_motors/motor_controller.py` delega al nodo ROS nuevo.
No ejecutarlo en paralelo con el launch ni usar otros scripts GPIO simultáneamente.

## Destinos, QR y cancelación

El mapa se genera desde cero en cada arranque. No hay relocalización sobre un mapa
persistente. Para evitar enviar el robot a coordenadas de otra sesión, cada destino
guarda un `map_session` y se rechaza si no coincide con la sesión actual.
Los ejemplos antiguos `scripts/saved_points.yaml` no se cargan automáticamente.

```bash
rosrun my_slam_setup save_points.py
```

En RViz añadir una herramienta `2D Nav Goal` para registrar destinos y cambiar su
topic a `/myhealthkit/save_point`. Esta herramienta guarda el punto sin mover el
robot. El fichero por defecto es `~/.ros/myhealthkit/saved_points.yaml`; los IDs
asignados aparecen en el log. Se puede configurar otra ruta compartida:

```bash
rosparam set /myhealthkit/points_file /ruta/absoluta/saved_points.yaml
rosrun my_slam_setup go_to_point.py 1
rosrun my_slam_setup go_to_point.py 1 --wait --timeout 180
rosrun my_slam_setup cancel_movement.py
```

Sin `--wait`, el comando confirma aceptación por `move_base`, no llegada.
Con `--wait` termina con error si falla, se cancela o se agota el plazo.
La cancelación solicita cancelar todos los objetivos; verificar `/move_base/status`
y `/cmd_vel` para observar el resultado. También se puede enviar un objetivo normal
desde otra herramienta RViz usando `/move_base_simple/goal`.

La app envía `{"message":"location1"}` a `/request-myhealthkit`. Ahora esa ruta
envía realmente el objetivo y responde HTTP 202 si se acepta, 400 si el JSON/QR es
inválido y 503 si no puede enviarlo. Admite IDs de varias cifras.
Arrancar Flask desde una terminal que haya cargado `devel/setup.bash`; no basta con
tener ROS abierto en otra terminal. Se conservan los demás requisitos del servidor
(modelos, claves y dependencias de audio/IA). La respuesta HTTP no sigue el progreso:
consultar los topics de estado de `move_base` para distinguir llegada y aborto.

## Pérdidas de datos y límites

El driver de motores deshabilita STBY si caduca `/cmd_vel` (0.3 s) o el latido de
localización (0.2 s). Usa reloj monotónico, incluso si se detiene el tiempo ROS.
La localización declara fallo ante scans/poses ausentes durante 0.5 s, saltos
inverosímiles o pose inválida. Ese fallo queda enclavado: inspeccionar, detener el
launch completo y volver a arrancar. No se reanuda automáticamente un objetivo viejo.
Tras reiniciar, volver a registrar los destinos. No resetear Hector ni publicar
`/initialpose` mientras se está navegando.

La detección de fallos no demuestra que el scan matching sea correcto: una pose
equivocada pero plausible puede pasar los filtros. Evitar giros rápidos, cristales,
zonas con pocas referencias y pasillos repetitivos; tampoco se ven obstáculos fuera
del plano del láser. No hay loop closure ni recuperación global. No son garantías
de seguridad física: si el proceso GPIO o el sistema operativo se bloquea, hace falta
un corte físico de alimentación o un watchdog hardware para garantizar la parada.

## Verificación realizada y pendiente

Las pruebas locales usan Python sin ROS/GPIO y cubren geometría, timestamps,
saltos, filtrado, conversión a PWM, paradas y contrato QR. También se validan
sintaxis compatible con Python 3.8, XML y configuración YAML.
No se ha compilado catkin ni probado el LiDAR o los motores desde Windows.

En la Pi comprobar además: ausencia de publicadores TF duplicados, mapa estable,
planificación rodeando obstáculos, llegada/cancelación, parada al desconectar el
LiDAR y parada al terminar el nodo de localización. Hacer las pruebas de fallo con
las ruedas levantadas antes de circular. Ajustar límites y huella con las medidas reales.

Referencias primarias usadas para los parámetros:

- [HectorMappingRos.cpp](https://github.com/tu-darmstadt-ros-pkg/hector_slam/blob/noetic-devel/hector_mapping/src/HectorMappingRos.cpp)
- [DWAPlanner.cfg](https://github.com/ros-planning/navigation/blob/noetic-devel/dwa_local_planner/cfg/DWAPlanner.cfg)
- [Launch oficial del RPLidar C1](https://github.com/Slamtec/rplidar_ros/blob/master/launch/rplidar_c1.launch)
