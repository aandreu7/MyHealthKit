import { useRef, useState } from 'react';
import { Alert, Button, Pressable, Text, View, Image } from 'react-native';
import AskMedicineScreen from '@components/AskMedicineScreen';
import RequestAMyHealthKitScreen from '@components/RequestAMyHealthKit';
import ShowMedicinesScreen from '@components/ShowMedicinesScreen';
import AddMedicine from '@components/AddMedicine';
import { styles } from '@hooks/styles';

export default function App() {
  const [screen, setScreen] = useState<'home' | 'askMedicine' | 'addMedicine' | 'showMedicines' | 'requestAMyHealthKit'>('home');
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
      content = <ShowMedicinesScreen onBack={() => setScreen('home')} />;
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

