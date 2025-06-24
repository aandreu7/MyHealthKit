import { useRef, useState } from 'react';
import { Text, View, Image, Pressable } from 'react-native';
import AskMedicineScreen from '@components/AskMedicineScreen';
import RequestAMyHealthKitScreen from '@components/RequestAMyHealthKit';
import ShowMedicinesScreen from '@components/ShowMedicinesScreen';
import AddMedicine from '@components/AddMedicine';
import MedicineDetails from '@components/MedicineDetails'; 
import { styles } from '@hooks/styles';

type Screen =
  | 'home'
  | 'askMedicine'
  | 'addMedicine'
  | 'showMedicines'
  | 'requestAMyHealthKit'
  | 'medicineDetails';

export default function App() {
  const [screen, setScreen] = useState<Screen>('home');
  const [selectedMedicineId, setSelectedMedicineId] = useState<string | null>(null);
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
            <Pressable style={styles.customButton} onPress={() => setScreen('addMedicine')}>
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
      content = <AskMedicineScreen onBack={() => setScreen('home')} setScreen={setScreen} />;
      break;

    case 'addMedicine':
      content = <AddMedicine onBack={() => setScreen('home')} />;
      break;

    case 'showMedicines':
      content = (
        <ShowMedicinesScreen
          onBack={() => setScreen('home')}
          onShowMedicineDetails={(medicineId: string) => {
            console.log('➡️ Selected medicineId:', medicineId); // ← AÑADE ESTO
            setSelectedMedicineId(medicineId);
            setTimeout(() => setScreen('medicineDetails'), 0);
          }}
        />
      );
      break;

    case 'medicineDetails':
      content = (
        <MedicineDetails
          medicineId={selectedMedicineId}
          onBack={() => setScreen('showMedicines')}
        />
      );
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
