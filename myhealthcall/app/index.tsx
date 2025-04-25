import { useRef, useState } from 'react';
import { Alert, Button, StyleSheet, Pressable, Text, View, Image } from 'react-native';
import AskMedicineScreen from '@components/AskMedicineScreen';
import RequestAMyHealthKitScreen from '@components/RequestAMyHealthKit';

export default function App() {
  const [screen, setScreen] = useState<'home' | 'askMedicine' | 'requestAMyHealthKit'>('home');
  const hasScannedRef = useRef(false);

  let content;

  switch (screen) {
    case 'home':
      content = (
        <View style={styles.container}>
          <Image
            source={require('@assets/images/logo.jpg')}
            style={styles.image}
          />
          <View style={styles.buttonContainer}>
            <Pressable style={styles.customButton} onPress={() => setScreen('requestAMyHealthKit')}>
              <Text style={styles.buttonText}>Request a MyHealthKit</Text>
            </Pressable>
  
            <Pressable style={styles.customButton} onPress={() => setScreen('askMedicine')}>
              <Text style={styles.buttonText}>Ask for a medicine</Text>
            </Pressable>
  
            <Pressable style={styles.customButton} onPress={() => {}}>
              <Text style={styles.buttonText}>Add a medicine</Text>
            </Pressable>
          </View>
        </View>
      );
      break;

    case 'requestAMyHealthKit':
        content = <RequestAMyHealthKitScreen onBack={() => setScreen('home')} />;
        break;
  
    case 'askMedicine':
      content = <AskMedicineScreen onBack={() => setScreen('home')} />;
      break;
  
    default:
      content = (
        <View style={styles.container}>
          <Text>Screen not found</Text>
        </View>
      );
  }
  
  return <View style={{ flex: 1 }}>{content}</View>;
}  

export const styles = StyleSheet.create({
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
