// components/AskMedicineScreen.tsx

import { Alert, View, Text, Pressable, StyleSheet, Image } from 'react-native';
import { sendMessageToRobot, Message2Robot } from '@/services/sendMessage2Robot';

type Props = {
  onBack: () => void;
};
 
const handleDiagnosis = async () => {
  const result = await sendMessageToRobot(Message2Robot.StartDiagnosis);
  if (result.success) {
    Alert.alert("Diagnosis started", "Don't worry, there's always a MyHealthKit looking after you!");
  } else {
    Alert.alert('Error', result.error || 'Diagnosis could not be started');
  }
};

export default function AskMedicineScreen({ onBack }: Props) {
  return (
    <View style={styles.container}>
      <Image
        source={require('@assets/images/logo.jpg')}
        style={styles.image}
      />
      <View style={styles.buttonContainer}>
        <Pressable style={styles.customButton} onPress={handleDiagnosis}>
          <Text style={styles.buttonText}>Get a diagnosis</Text>
        </Pressable>

        <Pressable style={styles.customButton} onPress={() => {}}>
          <Text style={styles.buttonText}>Select a medicine</Text>
        </Pressable>

        <Pressable style={[styles.customButton, { backgroundColor: '#aaa' }]} onPress={onBack}>
          <Text style={styles.buttonText}>Back</Text>
        </Pressable>
      </View>
    </View>
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
});
