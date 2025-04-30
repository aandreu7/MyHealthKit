// components/AskMedicineScreen.tsx
// @aandreu7

import { Alert, View, Text, Pressable, Image, ScrollView } from 'react-native';
import { sendMessageToRobot, Action2Robot } from '@/services/sendMessage2Robot';
import { useState } from 'react'
import { styles } from '@hooks/styles'

type Props = {
  onBack: () => void;
};

export default function ShowMedicinesScreen({ onBack }: Props) {

}