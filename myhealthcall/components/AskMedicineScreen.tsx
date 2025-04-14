// components/AskMedicineScreen.tsx

import { Alert, View, Text, Pressable, StyleSheet, Image } from 'react-native';
import { sendMessageToRobot } from '@/app/sendMessage2Robot';

type Props = {
  onBack: () => void;
};
 
const handleDiagnosis = async () => {
  const result = await sendMessageToRobot();
  if (result.success) {
    Alert.alert('Diagnóstico iniciado', 'El robot ha comenzado el proceso');
  } else {
    Alert.alert('Error', result.error || 'No se pudo iniciar el diagnóstico');
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
