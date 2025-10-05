import React, { useState, useEffect } from 'react';
import { View, Text, Pressable, Alert, ScrollView } from 'react-native';
import { sendMessageToRobot, Action2Robot } from '@/services/sendMessage2Robot';
import { styles } from '@hooks/styles';

type Props = {
  onBack: () => void;
  onShowMedicineDetails: (medicineId: string) => void;
};

type MedicineItem = {
  id: string;
  name: string;
};

export default function ShowMedicinesScreen({ onBack, onShowMedicineDetails }: Props) {
  const [medicines, setMedicines] = useState<MedicineItem[]>([]);
  const [loading, setLoading] = useState<boolean>(false);

  useEffect(() => {
    const fetchMedicines = async () => {
      setLoading(true);
      try {
        const response = await sendMessageToRobot(Action2Robot.ShowMedicines);
        if (response.success && response.medicine_items) {
          setMedicines(response.medicine_items);
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
  
  const handleSelectMedicine = (medicineId: string) => {
    onShowMedicineDetails(medicineId);
  };

  
  if (loading) {
    return (
      <View style={styles.center}>
        <Text style={styles.message}>Loading...</Text>
      </View>
    );
  }

  return (
    <View style={{ flex: 1 }}>
      <ScrollView contentContainerStyle={styles.container}>
        {medicines.length === 0 ? (
          <Text>No medicines available.</Text>
        ) : (
          medicines.map((medicine) => (
            <Pressable
              key={medicine.id}
              style={styles.customButton}
              onPress={() => handleSelectMedicine(medicine.id)}
            >
              <Text style={styles.buttonText}>{medicine.name}</Text>
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
