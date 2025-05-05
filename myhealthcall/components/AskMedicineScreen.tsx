// components/AskMedicineScreen.tsx
// @aandreu7

import { Alert, View, Text, Pressable, Image, ScrollView } from 'react-native';
import { sendMessageToRobot, Action2Robot } from '@/services/sendMessage2Robot';
import { useState } from 'react'
import { Audio } from 'expo-av';
import { styles } from '@hooks/styles'

type Props = {
  onBack: () => void;
  setScreen: React.Dispatch<React.SetStateAction<'home' | 'askMedicine' | 'addMedicine' | 'showMedicines' | 'requestAMyHealthKit'>>;
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

export default function AskMedicineScreen({ onBack, setScreen }: Props) {
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

        <Pressable
          style={styles.customButton}
          onPress={() => setScreen('showMedicines')}
        >
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
