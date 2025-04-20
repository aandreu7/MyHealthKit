// components/AskMedicineScreen.tsx
// @aandreu7

import { Alert, View, Text, Pressable, StyleSheet, Image, ScrollView } from 'react-native';
import { sendMessageToRobot, Action2Robot } from '@/services/sendMessage2Robot';
import { useState } from 'react'
import { Audio } from 'expo-av';

type Props = {
  onBack: () => void;
};

/*
  // Function to play the recorded audio
  const playAudio = async (uri) => {
    if (sound) {
      await sound.unloadAsync(); // Make sure to unload the previous sound if there was one
    }
    const { sound } = await Audio.Sound.createAsync(
      { uri: uri }, // Pass the URI of the file
      { shouldPlay: true } // Automatically play it
    );
    setSound(sound);
    console.log('Playing audio...');
  };
*/

export default function AskMedicineScreen({ onBack }: Props) {
  const [permissionResponse, requestPermission] = Audio.usePermissions();
  const [recording, setRecording] = useState();

  const [diagnosisMessage, setDiagnosisMessage] = useState<string | null>(null);
  const [suggestedMedicines, setSuggestedMedicines] = useState<string[] | null>(null);

  // const [sound, setSound] = useState(null);

  async function startRecording() {
    try {
      if (permissionResponse?.status !== 'granted') {
        console.log('Requesting permission..');
        const newPermission = await requestPermission();
        if (newPermission.status !== 'granted') {
            console.warn('Permission not granted');
            return;
        }
      }

      await Audio.setAudioModeAsync({
        allowsRecordingIOS: true,
        playsInSilentModeIOS: true,
      });

      console.log('Starting recording..');
      const { recording } = await Audio.Recording.createAsync(
        Audio.RecordingOptionsPresets.HIGH_QUALITY
      );

      setRecording(recording);

      console.log('Recording started');
    } catch (err) {
      console.error('Failed to start recording', err);
    }
  }

  async function stopRecording(): Promise<string | null> {
    try {
      console.log('Stopping recording..');
      setRecording(undefined);
      await recording.stopAndUnloadAsync();
      await Audio.setAudioModeAsync(
        {
            allowsRecordingIOS: false,
        }
      );

      const uri = recording.getURI();
      console.log('Recording stopped and stored at', uri);

      return uri;

    } catch (err) {
      console.error('Failed to stop recording', err);
      return null;
    }
  }

  const handleDiagnosis = async () => {
    try {
      if (!recording) {
        await startRecording();
      } else {
        const uri = await stopRecording();
        if (uri) {
            const response = await sendMessageToRobot(Action2Robot.StartDiagnosis, undefined, uri);
            console.log(response);
            if (response.success) {
                setDiagnosisMessage(response.message);
                setSuggestedMedicines(response.medicines);
            }
            else {
                Alert.alert("Error", "MyHealthKit could not answer.");
            }
        } else {
            Alert.alert("Error", "There was an issue with the voice recognition.");
        }
      }
    } catch (error) {
      Alert.alert("Error", "There was an issue with the voice recognition.");
    }
  };

  return (
    <ScrollView contentContainerStyle={styles.container}>
      <Image
        source={require('@assets/images/logo.jpg')}
        style={styles.image}
      />
      <View style={styles.buttonContainer}>
        <Pressable
          style={styles.customButton}
          onPress={handleDiagnosis}
        >
          <Text style={styles.buttonText}>{recording ? 'Recording...' : 'Get a diagnosis'}</Text>
        </Pressable>

        <Pressable style={styles.customButton} onPress={() => {}}>
          <Text style={styles.buttonText}>Select a medicine</Text>
        </Pressable>

        <Pressable style={[styles.customButton, { backgroundColor: '#aaa' }]} onPress={onBack}>
          <Text style={styles.buttonText}>Back</Text>
        </Pressable>
      </View>

      {diagnosisMessage && (
        <View style={styles.resultContainer}>
          <Text style={styles.resultTitle}>Diagnosis Result:</Text>
          <Text style={styles.resultText}>{diagnosisMessage}</Text>

          {suggestedMedicines && suggestedMedicines.length > 0 && (
            <View style={styles.medicinesList}>
              <Text style={styles.resultTitle}>Suggested Medicines:</Text>
              {suggestedMedicines.map((med, index) => (
                <Text key={index} style={styles.medicineItem}>• {med}</Text>
              ))}
            </View>
          )}
        </View>
      )}
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  image: {
    width: 200,
    height: 200,
    resizeMode: 'contain',
    alignSelf: 'center',
    marginBottom: 30,
  },
  container: {
    flex: 1,
    justifyContent: 'flex-start',
    alignItems: 'center',
    paddingHorizontal: 24,
    paddingVertical: 32,
    backgroundColor: '#f2f2f2',
    gap: 20,
  },
  buttonContainer: {
    flexDirection: 'column',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 10,
  },
  customButton: {
    backgroundColor: '#4da6ff',
    paddingVertical: 12,
    paddingHorizontal: 24,
    borderRadius: 10,
    marginVertical: 5,
    alignItems: 'center',
  },
  buttonText: {
    color: 'white',
    fontSize: 16,
    fontWeight: 'bold',
  },
  resultContainer: {
    marginTop: 30,
    padding: 20,
    backgroundColor: '#fff',
    borderRadius: 10,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.2,
    shadowRadius: 4,
    elevation: 4,
  },
  resultTitle: {
    fontSize: 18,
    fontWeight: 'bold',
    marginBottom: 10,
  },
  resultText: {
    fontSize: 16,
    marginBottom: 10,
    lineHeight: 22,
  },
  medicinesList: {
    marginTop: 10,
  },
  medicineItem: {
    fontSize: 16,
    marginLeft: 10,
    marginBottom: 5,
  },
});
