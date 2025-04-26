// components/AddMedicine.tsx
// @aandreu7

import React, { useState, useRef, useEffect } from 'react';
import { View, Text, Pressable, StyleSheet, ActivityIndicator } from 'react-native';
import { CameraView, useCameraPermissions } from 'expo-camera';
import { styles as appStyles } from '@hooks/styles';
import { sendMessageToRobot, Action2Robot } from '@/services/sendMessage2Robot';

type Props = {
  onBack: () => void;
};

export default function AddMedicine({ onBack }: Props) {
  const [permission, requestPermission] = useCameraPermissions();
  const [serverMessage, setServerMessage] = useState<string | null>(null);
  const [uploading, setUploading] = useState<boolean>(false); // 👈 NUEVO estado
  const cameraRef = useRef<any>(null);

  useEffect(() => {
    if (!permission?.granted) {
      requestPermission();
    }
  }, []);

  const takePicture = async () => {
    if (cameraRef.current) {
      const photo = await cameraRef.current.takePictureAsync();
      setUploading(true); // 👈 Cuando empieza a subir
      try {
        const response = await sendMessageToRobot(
          Action2Robot.AddMedicine,
          undefined,
          photo.uri
        );
        if (response.success && response.message) {
          setServerMessage(response.message);
        } else {
          setServerMessage('Failed to add the medicine.');
        }
      } catch (error) {
        console.error('Failed to send photo:', error);
        setServerMessage('Error sending the photo.');
      } finally {
        setUploading(false); // 👈 Cuando termina de subir
      }
    }
  };

  if (!permission) return <View />;

  if (!permission.granted) {
    return (
      <View style={appStyles.container}>
        <Text style={appStyles.text}>
          We need your permission to use the camera
        </Text>
        <Pressable style={appStyles.customButton} onPress={requestPermission}>
          <Text style={appStyles.buttonText}>Grant Permission</Text>
        </Pressable>
      </View>
    );
  }

  // 👇 Si estamos subiendo la imagen, mostramos "Uploading..."
  if (uploading) {
    return (
      <View style={styles.center}>
        <ActivityIndicator size="large" color="#0000ff" />
        <Text style={styles.message}>Uploading photo...</Text>
      </View>
    );
  }

  // Si ya tenemos mensaje del servidor, lo mostramos
  if (serverMessage) {
    return (
      <View style={styles.center}>
        <Text style={styles.message}>{serverMessage}</Text>
        <Pressable style={appStyles.customButton} onPress={onBack}>
          <Text style={appStyles.buttonText}>Back</Text>
        </Pressable>
      </View>
    );
  }

  // Muestra la cámara si no hay mensaje aún
  return (
    <View style={{ flex: 1 }}>
      <CameraView
        ref={cameraRef}
        style={{ flex: 1 }}
        facing="environment"
      />
      <View style={styles.controls}>
        <Pressable style={appStyles.customButton} onPress={onBack}>
          <Text style={appStyles.buttonText}>Back</Text>
        </Pressable>
        <Pressable style={appStyles.customButton} onPress={takePicture}>
          <Text style={appStyles.buttonText}>Capture</Text>
        </Pressable>
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  center: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
  },
  controls: {
    position: 'absolute',
    bottom: 40,
    flexDirection: 'row',
    width: '100%',
    justifyContent: 'space-between',
    paddingHorizontal: 30,
  },
  message: {
    fontSize: 18,
    textAlign: 'center',
    marginBottom: 20,
    paddingHorizontal: 20,
  },
});
