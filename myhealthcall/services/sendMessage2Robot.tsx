import * as FileSystem from 'expo-file-system';

export const ROBOT_IP = 'http://192.168.1.176:5000';

export const enum Action2Robot {
  StartDiagnosis = 'start-diagnosis',
  AskMedicine = 'ask-medicine',
  AddMedicine = 'add-medicine',
  ShowMedicines = 'show-medicines',
  ReleaseMedicine = 'release-medicine',
  MedicineDetails = 'medicine-details',
  RequestMyHealthKit = 'request-myhealthkit'
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
): Promise<{
  success: boolean,
  error?: string,
  message?: string,
  medicines?: string[],
  existing_medicines?: any,
  name?: string,
  description?: string,
  url_prospect?: string,
  symptoms?: string,
  contraindications?: string,
  audioUri?: string,
}> => {
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
      case Action2Robot.MedicineDetails:
        url += `/medicine-details`;
        break;
      case Action2Robot.RequestMyHealthKit:
        url += '/request-myhealthkit';
        break;
      default:
        return { success: false, error: 'Unknown action.' };
    }

    let response: any;

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
        response = await fetch(url, { method: 'GET' });
      } else if (action === Action2Robot.ReleaseMedicine) {
        response = await fetch(url, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ medicine_id: message })
        });
      } else if (action === Action2Robot.MedicineDetails) {
        response = await fetch(url, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ name: message })
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

    if (action === Action2Robot.AddMedicine && uri && response && response.body) {
      try {
        const dataAnswer = JSON.parse(response.body);
        return { success: true, message: dataAnswer.message };
      } catch (e) {
        return { success: false, error: "Could not parse server response as JSON: " + response.body };
      }
    }

    console.log("Server response: ", response);

    if (response && (response.ok || (response.status >= 200 && response.status < 300))) {
      let dataAnswer;
      try {
        if (action == Action2Robot.StartDiagnosis) {
            dataAnswer = JSON.parse(response.body);
        }
        else {
            dataAnswer = await response.json();
        }
      } catch (error) {
        const text = await response.text();
        return { success: false, error: "Could not parse server response as JSON: " + text };
      }

      switch (action) {
        case Action2Robot.StartDiagnosis:
          return {
            success: true,
            audioUri: dataAnswer.audioUri,
            message: dataAnswer.message,
            medicines: dataAnswer.medicines
          };
        case Action2Robot.AddMedicine:
          return { success: true, message: dataAnswer.message };
        case Action2Robot.ShowMedicines:
          return { success: true, message: dataAnswer.message, medicines: dataAnswer.medicines };
        case Action2Robot.ReleaseMedicine:
          return { success: true, message: dataAnswer.message };
        case Action2Robot.MedicineDetails:
          return {
            success: true,
            name: dataAnswer.name,
            description: dataAnswer.description,
            url_prospect: dataAnswer.url_prospect,
            symptoms: dataAnswer.symptoms,
            contraindications: dataAnswer.contraindications
          };
        default:
          return { success: true, message: dataAnswer.message };
      }
    } else {
      let errorText = "";
      try {
        errorText = await response.text();
        console.error("Server response error:", errorText);
      } catch (err) {
        errorText = "Error in the response from the server.";
      }
      return { success: false, error: errorText || 'Error in the response from the server.' };
    }
  } catch (error) {
    console.error("Error sending message to robot:", error);
    return { success: false, error: 'Connection could not be established.' };
  }
};
