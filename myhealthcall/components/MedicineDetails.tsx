import React, { useEffect, useState } from 'react';
import { View, Text, Pressable, ActivityIndicator, ScrollView, Linking } from 'react-native';
import { sendMessageToRobot, Action2Robot } from '@/services/sendMessage2Robot';
import { styles } from '@hooks/styles';

type Props = {
  medicineName: string | null;
  onBack: () => void;
};

export default function MedicineDetails({ medicineName, onBack }: Props) {
  const [loading, setLoading] = useState(true);
  const [details, setDetails] = useState<any>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!medicineName) return;
    const fetchDetails = async () => {
      setLoading(true);
      setError(null);
      try {
        const response = await sendMessageToRobot(Action2Robot.MedicineDetails, medicineName);
        if (response.success) {
          setDetails(response);
        } else {
          setError(response.error || 'Error loading medicine details.');
        }
      } catch (e) {
        setError('Error fetching medicine details');
      } finally {
        setLoading(false);
      }
    };
    fetchDetails();
  }, [medicineName]);

  if (!medicineName) {
    return (
      <View style={styles.center}>
        <Text style={styles.message}>No medicine selected.</Text>
        <Pressable style={styles.customButton} onPress={onBack}>
          <Text style={styles.buttonText}>Back</Text>
        </Pressable>
      </View>
    );
  }

  if (loading) {
    return (
      <View style={styles.center}>
        <ActivityIndicator size="large" color="#38bdf8" />
        <Text style={[styles.message, { marginTop: 10 }]}>Loading details...</Text>
      </View>
    );
  }

  if (error) {
    return (
      <View style={styles.center}>
        <Text style={[styles.message, { color: '#dc2626' }]}>{error}</Text>
        <Pressable style={styles.customButton} onPress={onBack}>
          <Text style={styles.buttonText}>Back</Text>
        </Pressable>
      </View>
    );
  }

  if (!details) {
    return (
      <View style={styles.center}>
        <Text style={styles.message}>No details found.</Text>
        <Pressable style={styles.customButton} onPress={onBack}>
          <Text style={styles.buttonText}>Back</Text>
        </Pressable>
      </View>
    );
  }

  return (
    <ScrollView contentContainerStyle={{
      flexGrow: 1,
      justifyContent: 'center',
      alignItems: 'center',
      padding: 20
    }}>
      <View
        style={{
          backgroundColor: 'white',
          borderRadius: 16,
          shadowColor: '#000',
          shadowOffset: { width: 0, height: 2 },
          shadowOpacity: 0.18,
          shadowRadius: 8,
          elevation: 4,
          padding: 24,
          marginBottom: 20,
          width: '100%',
          maxWidth: 420,
        }}
      >
        <Text style={{
          fontSize: 28,
          fontWeight: 'bold',
          marginBottom: 16,
          color: '#0ea5e9',
          textAlign: 'center'
        }}>
          {details.name || 'No name'}
        </Text>
        <InfoRow label="Description" value={details.description} />
        <InfoRow label="Symptoms" value={details.symptoms} />
        <InfoRow label="Contraindications" value={details.contraindications} />
        <View style={{ marginTop: 8, marginBottom: 10 }}>
          <Text style={{ fontWeight: 'bold', fontSize: 16 }}>URL Prospect:</Text>
          {details.url_prospect ? (
            <Text
              style={{
                color: '#2563eb',
                textDecorationLine: 'underline',
                fontSize: 15,
                marginTop: 2
              }}
              selectable
              onPress={() => Linking.openURL(details.url_prospect)}
            >
              {details.url_prospect}
            </Text>
          ) : (
            <Text style={{ color: '#64748b', fontSize: 15 }}>N/A</Text>
          )}
        </View>
      </View>

      <Pressable style={[styles.customButton, { width: 180 }]} onPress={onBack}>
        <Text style={styles.buttonText}>Back</Text>
      </Pressable>
    </ScrollView>
  );
}

// Helper para mostrar cada campo
function InfoRow({ label, value }: { label: string; value?: string }) {
  return (
    <View style={{ marginBottom: 10 }}>
      <Text style={{ fontWeight: 'bold', fontSize: 16 }}>{label}:</Text>
      <Text style={{ color: '#334155', fontSize: 15 }}>
        {value && value.trim() ? value : 'N/A'}
      </Text>
    </View>
  );
}
