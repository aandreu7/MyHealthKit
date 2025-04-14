import { CameraView, useCameraPermissions, BarcodeScanningResult } from 'expo-camera';
import { useRef, useState } from 'react';
import { Alert, Button, StyleSheet, Pressable, Text, View, Image } from 'react-native';
import AskMedicineScreen from '@components/AskMedicineScreen';

export default function App() {
  const [permission, requestPermission] = useCameraPermissions();
  const [cameraVisible, setCameraVisible] = useState(false);
  const [screen, setScreen] = useState<'home' | 'askMedicine'>('home');
  const hasScannedRef = useRef(false);


  if (!permission) return <View />;
  if (!permission.granted) {
    return (
      <View style={styles.container}>
        <Text style={styles.container}>We need your permission to show the camera</Text>
        <Button onPress={requestPermission} title="Grant permission" />
      </View>
    );
  }

  const handleBarCodeScanned = (scanningResult: BarcodeScanningResult) => {
    if (!hasScannedRef.current) {
      hasScannedRef.current = true; // Evita múltiples llamadas
      Alert.alert('A MyHealthKit is on its way.', '', [
        {
          text: 'OK',
          onPress: () => {
            setCameraVisible(false);
            hasScannedRef.current = false; // Lo reseteamos para volver a escanear más tarde
          },
        },
      ]);
    }
  };
  
  if (cameraVisible) {
    return (
      <CameraView
        style={{ flex: 1 }}
        facing="back"
        barcodeScannerSettings={{ barcodeTypes: ['qr'] }}
        onBarcodeScanned={handleBarCodeScanned}
      />
    );
  }

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
            <Pressable style={styles.customButton} onPress={() => setCameraVisible(true)}>
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
