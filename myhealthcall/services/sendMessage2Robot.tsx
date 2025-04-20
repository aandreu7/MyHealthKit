// services/recordVoice.tsx
// @aandreu7

import * as FileSystem from 'expo-file-system';

//export const ROBOT_IP = 'https://192.168.1.167:5000';
export const ROBOT_IP = 'http://192.168.1.167:5000';
//export const ROBOT_IP = 'https://myhealthcontroller.duckdns.org';

export const enum Action2Robot {
    StartDiagnosis = 'start-diagnosis',
    AskMedicine = 'ask-medicine',
    AddMedicine = 'add-medicine',
}

const fetchWithTimeout = (url: string, options: RequestInit, timeout: number = 3000): Promise<Response> => {
    const controller = new AbortController();
    const id = setTimeout(() => controller.abort(), timeout);

    return fetch(url, options).finally(() => clearTimeout(id)).catch((error) => {
        console.error("Error sending ping:", error); throw error;
    });
};

export const sendMessageToRobot = async (action: Action2Robot, message?: string, uri?: string): Promise<{ success: boolean, error?: string, message?: string, medicines?: string[] }> => {
    try {
        const ping = await fetchWithTimeout(ROBOT_IP, {});

        if (ping.ok) {
            let url: string = `${ROBOT_IP}`;
            switch (action) {
                case 'start-diagnosis':
                url = url + `/start-diagnosis`;
                break;
                case 'ask-medicine':
                url = url + `/ask-medicine`;
                break;
                case 'add-medicine':
                url = url + `/add-medicine`;
                break;
                default:
                return { success: false, error: 'Unknown action.' };
            }

            let response;

            if (uri) { // PREBUILT MESSAGE
                try {
                     if (action == 'start-diagnosis') {
                         response = await FileSystem.uploadAsync(url, uri!, {
                           fieldName: 'file',
                           httpMethod: 'POST',
                           uploadType: FileSystem.FileSystemUploadType.MULTIPART,
                           mimeType: 'audio/m4a',
                           parameters: {
                           },
                         });
                     }
                 } catch(error) {
                     console.log("Error uploading file:", error);
                 }
            }

            else { // MESSAGE TO BE BUILT
                const headers: HeadersInit = {
                    'Content-Type': 'application/json',
                };
                let body: any;

                if (message instanceof FormData) {
                    body = message;
                } else {
                    body = JSON.stringify({ message });
                }

                response = await fetch(url, {
                    method: 'POST',
                    body: body,
                });
            }

            const isSuccessful = response.status && response.status >= 200 && response.status < 300 || (response.ok !== undefined && response.ok);
            if (isSuccessful) {
                let dataAnswer;

                try {
                    if (typeof response.json === 'function') {
                      dataAnswer = await response.json();
                    } else if (response.body) {
                      dataAnswer = JSON.parse(response.body);
                    }
                } catch (error) {
                    console.log("Error parsing server's response:", error);
                }

                switch (action) {
                    case 'start-diagnosis':
                    return {
                        success: true,
                        message: dataAnswer.message,
                        medicines: dataAnswer.medicines
                    };
                    break;
                }
            }
            else {
                return { success: false, error: 'Error at the answer.' };
            }
        } else {
        return { success: false, error: 'MyHealthKit is not reachable or responded with an error (ping did not reach).' };
        }
    } catch (error) {
        return { success: false, error: 'Connection could not be established.' };
    }
};