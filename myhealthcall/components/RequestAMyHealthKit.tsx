// components/RequestAMyHealthKit.tsx
// @aandreu7

import React, { useState, useRef, useEffect } from 'react';
import { Alert, View, Text, Pressable, StyleSheet, Image, ScrollView, Button } from 'react-native';
import { CameraView, useCameraPermissions, BarcodeScanningResult } from 'expo-camera';
import { styles } from '@hooks/styles'
import { Action2Robot, sendMessageToRobot } from '@services/sendMessage2Robot';

type Props = {
  onBack: () => void;
};

export default function RequestAMyHealthKitScreen({ onBack }: Props) {
  const [permission, requestPermission] = useCameraPermissions();
  const [cameraVisible, setCameraVisible] = useState(false);
  const [serverMessage, setServerMessage] = useState<string | null>(null);
  const hasScannedRef = useRef(false);

  useEffect(() => {
    if (permission?.granted) {
      setCameraVisible(true);
    }
  }, [permission]);

  const handleBarCodeScanned = async (scanningResult: BarcodeScanningResult) => {
    if (!hasScannedRef.current) {
      try {
        hasScannedRef.current = true;
        const response = await sendMessageToRobot(
          Action2Robot.RequestMyHealthKit,
          scanningResult.data,
          undefined
        );
        if (response.success) {
          Alert.alert('A MyHealthKit is on its way.', '', [
            {
              text: 'OK',
              onPress: () => {
                setCameraVisible(false);
                hasScannedRef.current = false;
                onBack();
              },
            },
          ]);
        }else if (response.error) {
          setServerMessage(response.error);
        } else {
          setServerMessage('Failed to request a MyHealthKit.');
        }
      } catch (error) {
        console.error('Failed to request a MyHealthKit: ', error);
        setServerMessage('Error requesting a MyHealthKit.');
      } finally {
        setCameraVisible(false);
        hasScannedRef.current = false;
      }
    }
  };

  if (!permission) return <View />;
  if (!permission.granted) {
    return (
      <View style={styles.container}>
        <Text style={styles.text}>We need your permission to show the camera</Text>
        <Button onPress={requestPermission} title="Grant permission" />
      </View>
    );
  }

  if (cameraVisible) {
    return (
      <View style={{ flex: 1 }}>
        <CameraView
          style={{ flex: 1 }}
          facing="back"
          barcodeScannerSettings={{ barcodeTypes: ['qr'] }}
          onBarcodeScanned={handleBarCodeScanned}
        />
        <Pressable
          onPress={onBack}
          style={styles.customButton}
        >
          <Text style={styles.buttonText}>Volver</Text>
        </Pressable>
      </View>
    );
  }

  // If we already have a response from server, we show it
  if (serverMessage) {
    return (
      <View style={styles.center}>
        <Text style={styles.message}>{serverMessage}</Text>
        <Pressable style={styles.customButton} onPress={onBack}>
          <Text style={styles.buttonText}>Back</Text>
        </Pressable>
      </View>
    );
  }

}
