export const ROBOT_IP = 'http://192.168.1.167:5000';

export const enum Message2Robot {
    StartDiagnosis = 'start-diagnosis',
    AskMedicine = 'ask-medicine',
    AddMedicine = 'add-medicine',
}

const fetchWithTimeout = (url: string, options: RequestInit, timeout: number) => {
    return new Promise<Response>(async (resolve, reject) => {
      const timer = setTimeout(() => reject(new Error('Request timed out')), timeout);
      try {
        const response = await fetch(url, options);
        clearTimeout(timer);
        resolve(response);
      } catch (error) {
        clearTimeout(timer);
        reject(error);
      }
    });
};

export const sendMessageToRobot = async (action: Message2Robot): Promise<{ success: boolean, error?: string }> => {
    try {

        const pingTimeout = 3000; // 3 seconds timeout
        const ping = await fetchWithTimeout(ROBOT_IP, {}, pingTimeout);
        
        if (ping.ok) {
        let url: string = `${ROBOT_IP}`;
        switch (action) {
            case 'start-diagnosis':
            url = url + `/start-diagnosis`;
            break;
            case 'ask-medicine':
            url = url + `/stop-diagnosis`;
            break;
            case 'add-medicine':
            url = url + `/add-medicine`;
            break;
            default:
            return { success: false, error: 'Unknown action.' };
        }

        const response = await fetch(url, {
            method: 'POST',
        });

        if (response.ok) {
            return { success: true };
        } else {
            return { success: false, error: 'Error sending command.' };
        }
        } else {
        return { success: false, error: 'MyHealthKit is not reachable or responded with an error.' };
        }
    } catch (error) {
        return { success: false, error: 'Connection could not be established.' };
    }
};