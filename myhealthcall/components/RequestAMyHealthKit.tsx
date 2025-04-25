// components/RequestAMyHealthKit.tsx
// @aandreu7

import React, { useState, useRef, useEffect } from 'react';
import { Alert, View, Text, Pressable, StyleSheet, Image, ScrollView, Button } from 'react-native';
import { CameraView, useCameraPermissions, BarcodeScanningResult } from 'expo-camera';
import { styles } from '@hooks/styles'

type Props = {
  onBack: () => void;
};

export default function RequestAMyHealthKitScreen({ onBack }: Props) {
  const [permission, requestPermission] = useCameraPermissions();
  const [cameraVisible, setCameraVisible] = useState(false);
  const hasScannedRef = useRef(false);

  useEffect(() => {
    if (permission?.granted) {
      setCameraVisible(true);
    }
  }, [permission]);

  const handleBarCodeScanned = (scanningResult: BarcodeScanningResult) => {
    if (!hasScannedRef.current) {
      hasScannedRef.current = true;
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

}
