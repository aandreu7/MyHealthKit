import * as FileSystem from 'expo-file-system';

export const ROBOT_IP = 'http://192.168.1.135:5000';

export const enum Action2Robot {
  StartDiagnosis = 'start-diagnosis',
  AskMedicine = 'ask-medicine',
  AddMedicine = 'add-medicine',
  ShowMedicines = 'show-medicines',
  ReleaseMedicine = 'release-medicine'
}

const fetchWithTimeout = (url: string, options: RequestInit, timeout: number = 3000): Promise<Response> => {
  const controller = new AbortController();
  const signal = controller.signal;
  const timeoutId = setTimeout(() => controller.abort(), timeout);

  return fetch(url, { ...options, signal })
    .then((response) => response)
    .catch((error) => {
      if (error.name === 'AbortError') {
        console.error(`Request timed out: ${timeout} ms`);
      } else if (error.message.includes("Network request timed out")) {
        console.error("Network request timed out - Server likely unreachable.");
      } else {
        console.error('Request failed:', error);
      }
      throw error;
    })
    .finally(() => clearTimeout(timeoutId));
};

export const sendMessageToRobot = async (
  action: Action2Robot,
  message?: string,
  uri?: string
): Promise<{ success: boolean, error?: string, message?: string, medicines?: string[], existing_medicines?: any }> => {
  try {
    const ping = await fetchWithTimeout(ROBOT_IP, {});

    if (!ping.ok) {
      return { success: false, error: 'MyHealthKit is not reachable or responded with an error (ping did not reach).' };
    }

    let url = `${ROBOT_IP}`;
    switch (action) {
      case Action2Robot.StartDiagnosis:
        url += `/start-diagnosis`;
        break;
      case Action2Robot.AskMedicine:
        url += `/ask-medicine`;
        break;
      case Action2Robot.AddMedicine:
        url += `/add-medicine`;
        break;
      case Action2Robot.ShowMedicines:
        url += `/show-medicines`;
        break;
      case Action2Robot.ReleaseMedicine:
        url += `/select-medicine`;
        break;
      default:
        return { success: false, error: 'Unknown action.' };
    }

    let response;

    if (uri) {
      if (action === Action2Robot.StartDiagnosis) {
        response = await FileSystem.uploadAsync(url, uri, {
          fieldName: 'file',
          httpMethod: 'POST',
          uploadType: FileSystem.FileSystemUploadType.MULTIPART,
          mimeType: 'audio/m4a',
          parameters: {},
        });
      } else if (action === Action2Robot.AddMedicine) {
        response = await FileSystem.uploadAsync(url, uri, {
          fieldName: 'file',
          httpMethod: 'POST',
          uploadType: FileSystem.FileSystemUploadType.MULTIPART,
          mimeType: 'image/jpeg',
          parameters: {},
        });
      }
    } else {
      if (action === Action2Robot.ShowMedicines) {
        response = await fetch(url, {
          method: 'GET',
          headers: { 'Content-Type': 'application/json' }
        });
      } else if (action === Action2Robot.ReleaseMedicine) {
        response = await fetch(url, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ medicine_id: message })
        });
      } else {
        const headers: HeadersInit = { 'Content-Type': 'application/json' };
        const body = message instanceof FormData ? message : JSON.stringify({ message });
        response = await fetch(url, {
          method: 'POST',
          headers,
          body
        });
      }
    }

    if (response && response.ok) {
      let dataAnswer;
      try {
        dataAnswer = typeof response.json === 'function' ? await response.json() : JSON.parse(response.body);
      } catch (error) {
        console.log("Error parsing server's response:", error);
      }

      switch (action) {
        case Action2Robot.StartDiagnosis:
          return { success: true, message: dataAnswer.message, medicines: dataAnswer.medicines };
        case Action2Robot.AddMedicine:
          return { success: true, message: dataAnswer.message };
        case Action2Robot.ShowMedicines:
          return { success: true, message: dataAnswer.message, medicines: dataAnswer.medicines };
        case Action2Robot.ReleaseMedicine:
          return { success: true, message: dataAnswer.message };
        default:
          return { success: true, message: dataAnswer.message };
      }
    } else {
      return { success: false, error: 'Error in the response from the server.' };
    }
  } catch (error) {
    return { success: false, error: 'Connection could not be established.' };
  }
};
