import React, { useState, useEffect } from 'react';
import { View, Text, Pressable, Alert, ScrollView } from 'react-native';
import { sendMessageToRobot, Action2Robot } from '@/services/sendMessage2Robot';
import { styles } from '@hooks/styles';

type Props = {
  onBack: () => void;
};

export default function ShowMedicinesScreen({ onBack }: Props) {
  const [medicines, setMedicines] = useState<string[]>([]);
  const [loading, setLoading] = useState<boolean>(false);

  useEffect(() => {
    const fetchMedicines = async () => {
      setLoading(true);
      try {
        const response = await sendMessageToRobot(Action2Robot.ShowMedicines);
        if (response.success && response.medicines) {
          setMedicines(response.medicines);
        } else {
          Alert.alert('Error', 'Could not load medicines.');
        }
      } catch (error) {
        console.error('Error loading medicines:', error);
        Alert.alert('Error', 'There was a problem loading medicines.');
      } finally {
        setLoading(false);
      }
    };

    fetchMedicines();
  }, []);

  const handleSelectMedicine = async (medicine: string) => {
    Alert.alert('Medicine selected', medicine, [
      {
        text: 'OK',
        onPress: async () => {
          setLoading(true);
          try {
            const response = await sendMessageToRobot(Action2Robot.ReleaseMedicine, medicine);
            if (response.success) {
              Alert.alert('Success', `Medicine '${medicine}' has been released.`);
            } else {
              Alert.alert('Error', `Could not release medicine '${medicine}'.`);
            }
          } catch (error) {
            console.error('Error releasing medicine:', error);
            Alert.alert('Error', 'There was a problem releasing the medicine.');
          } finally {
            setLoading(false);
          }
        },
      },
    ]);
  };

  if (loading) {
    return (
      <View style={styles.center}>
        <Text style={styles.message}>Loading medicines...</Text>
      </View>
    );
  }

  return (
    <View style={{ flex: 1 }}>
      <ScrollView contentContainerStyle={styles.container}>
        {medicines.length === 0 ? (
          <Text>No medicines available.</Text>
        ) : (
          medicines.map((medicine, index) => (
            <Pressable
              key={index}
              style={styles.customButton}
              onPress={() => handleSelectMedicine(medicine)}
            >
              <Text style={styles.buttonText}>{medicine}</Text>
            </Pressable>
          ))
        )}
      </ScrollView>
      <Pressable style={styles.customButton} onPress={onBack}>
        <Text style={styles.buttonText}>Back</Text>
      </Pressable>
    </View>
  );
}
