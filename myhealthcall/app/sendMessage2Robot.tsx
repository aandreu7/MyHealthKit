export const ROBOT_IP = 'http://192.168.1.167:5000'; // ejemplo

export const sendMessageToRobot = async () => {
  try {
    const ping = await fetch(ROBOT_IP);
    if (ping.ok) {
      const response = await fetch(`${ROBOT_IP}/start-diagnosis`, {
        method: 'POST',
      });

      if (response.ok) {
        return { success: true };
      } else {
        return { success: false, error: 'Error al enviar el comando' };
      }
    } else {
      return { success: false, error: 'El robot respondió con error' };
    }
  } catch (error) {
    return { success: false, error: 'No se pudo contactar con el robot' };
  }
};
