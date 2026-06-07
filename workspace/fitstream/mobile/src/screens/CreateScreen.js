/**
 * Create Screen — Main generation interface
 * Upload photo + write prompt → generate animation
 */

import React, { useState, useEffect } from 'react';
import {
  View, Text, TextInput, TouchableOpacity, Image,
  ScrollView, ActivityIndicator, Alert, StyleSheet,
} from 'react-native';
import * as ImagePicker from 'expo-image-picker';
import FitStreamAPI from '../services/api';

const api = new FitStreamAPI();

const MODES = [
  { id: 'animate', label: '📸 Animate', icon: '📸' },
  { id: 'story', label: '📖 Story', icon: '📖' },
  { id: 'style', label: '🎭 Style', icon: '🎭' },
];

const STYLES = [
  { id: 'cinematic', label: '🎬 Cinematic' },
  { id: 'ghibli', label: '🏯 Ghibli' },
  { id: 'pixar', label: '🧊 Pixar' },
  { id: 'comic', label: '💥 Comic' },
  { id: 'noir', label: '🌑 Noir' },
  { id: 'cyberpunk', label: '🌆 Cyberpunk' },
  { id: 'watercolor', label: '🎨 Watercolor' },
  { id: 'anime', label: '🎌 Anime' },
];

export default function CreateScreen() {
  const [image, setImage] = useState(null);
  const [prompt, setPrompt] = useState('');
  const [mode, setMode] = useState('animate');
  const [style, setStyle] = useState('cinematic');
  const [generating, setGenerating] = useState(false);
  const [status, setStatus] = useState('');
  const [videoUrl, setVideoUrl] = useState(null);

  const pickImage = async () => {
    const result = await ImagePicker.launchImageLibraryAsync({
      mediaTypes: ['images'],
      quality: 0.8,
      allowsEditing: true,
    });
    if (!result.canceled) {
      setImage(result.assets[0].uri);
    }
  };

  const generate = async () => {
    if (!image) return Alert.alert('Error', 'Please select an image');
    if (!prompt.trim()) return Alert.alert('Error', 'Please enter a prompt');

    setGenerating(true);
    setStatus('Submitting...');
    setVideoUrl(null);

    try {
      const { job_id } = await api.generate({
        imageUri: image,
        prompt,
        mode,
        style,
      });

      setStatus('Generating...');
      const result = await api.pollUntilDone(job_id);
      
      setVideoUrl(api.getVideoUrl(job_id));
      setStatus('Done!');
    } catch (e) {
      setStatus(`Error: ${e.message}`);
      Alert.alert('Generation Failed', e.message);
    } finally {
      setGenerating(false);
    }
  };

  return (
    <ScrollView style={s.container}>
      {/* Image Picker */}
      <TouchableOpacity style={s.imagePicker} onPress={pickImage}>
        {image ? (
          <Image source={{ uri: image }} style={s.previewImage} />
        ) : (
          <View style={s.placeholder}>
            <Text style={s.placeholderIcon}>📷</Text>
            <Text style={s.placeholderText}>Tap to select a photo</Text>
          </View>
        )}
      </TouchableOpacity>

      {/* Mode Selector */}
      <Text style={s.label}>MODE</Text>
      <ScrollView horizontal showsHorizontalScrollIndicator={false} style={s.chipRow}>
        {MODES.map(m => (
          <TouchableOpacity
            key={m.id}
            style={[s.chip, mode === m.id && s.chipActive]}
            onPress={() => setMode(m.id)}
          >
            <Text style={[s.chipText, mode === m.id && s.chipTextActive]}>{m.label}</Text>
          </TouchableOpacity>
        ))}
      </ScrollView>

      {/* Style Selector */}
      <Text style={s.label}>STYLE</Text>
      <ScrollView horizontal showsHorizontalScrollIndicator={false} style={s.chipRow}>
        {STYLES.map(st => (
          <TouchableOpacity
            key={st.id}
            style={[s.chip, style === st.id && s.chipActive]}
            onPress={() => setStyle(st.id)}
          >
            <Text style={[s.chipText, style === st.id && s.chipTextActive]}>{st.label}</Text>
          </TouchableOpacity>
        ))}
      </ScrollView>

      {/* Prompt */}
      <Text style={s.label}>PROMPT</Text>
      <TextInput
        style={s.input}
        placeholder="Describe the animation..."
        placeholderTextColor="#64748b"
        value={prompt}
        onChangeText={setPrompt}
        multiline
        numberOfLines={3}
      />

      {/* Generate Button */}
      <TouchableOpacity
        style={[s.button, generating && s.buttonDisabled]}
        onPress={generate}
        disabled={generating}
      >
        {generating ? (
          <ActivityIndicator color="#fff" />
        ) : (
          <Text style={s.buttonText}>🎬 Generate</Text>
        )}
      </TouchableOpacity>

      {/* Status */}
      {status ? (
        <View style={s.statusBar}>
          <Text style={s.statusText}>{status}</Text>
        </View>
      ) : null}

      {/* Video Result */}
      {videoUrl ? (
        <View style={s.resultCard}>
          <Text style={s.resultTitle}>✅ Video Ready</Text>
          <Text style={s.resultUrl}>{videoUrl}</Text>
        </View>
      ) : null}

      <View style={{ height: 40 }} />
    </ScrollView>
  );
}

const s = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#07070e', padding: 16 },
  imagePicker: {
    height: 200, borderRadius: 16, overflow: 'hidden',
    backgroundColor: 'rgba(255,255,255,0.04)',
    borderWidth: 2, borderColor: 'rgba(255,255,255,0.08)',
    borderStyle: 'dashed', marginBottom: 20,
  },
  previewImage: { width: '100%', height: '100%', resizeMode: 'cover' },
  placeholder: { flex: 1, alignItems: 'center', justifyContent: 'center' },
  placeholderIcon: { fontSize: 40, marginBottom: 8 },
  placeholderText: { color: '#64748b', fontSize: 14 },
  label: {
    fontSize: 11, fontWeight: '700', color: '#64748b',
    letterSpacing: 1, marginBottom: 8, marginTop: 4,
  },
  chipRow: { marginBottom: 16 },
  chip: {
    paddingHorizontal: 16, paddingVertical: 8, borderRadius: 20,
    backgroundColor: 'rgba(255,255,255,0.04)',
    borderWidth: 1, borderColor: 'rgba(255,255,255,0.08)',
    marginRight: 8,
  },
  chipActive: {
    backgroundColor: 'rgba(139,92,246,0.2)',
    borderColor: '#8b5cf6',
  },
  chipText: { color: '#94a3b8', fontSize: 13, fontWeight: '600' },
  chipTextActive: { color: '#a78bfa' },
  input: {
    backgroundColor: 'rgba(255,255,255,0.03)',
    borderWidth: 1, borderColor: 'rgba(255,255,255,0.08)',
    borderRadius: 12, padding: 14, color: '#f1f5f9',
    fontSize: 14, marginBottom: 20, minHeight: 80,
    textAlignVertical: 'top',
  },
  button: {
    backgroundColor: '#8b5cf6', borderRadius: 12,
    padding: 16, alignItems: 'center',
  },
  buttonDisabled: { opacity: 0.5 },
  buttonText: { color: '#fff', fontSize: 16, fontWeight: '800', letterSpacing: 1 },
  statusBar: {
    marginTop: 16, padding: 12, borderRadius: 12,
    backgroundColor: 'rgba(139,92,246,0.1)',
    borderWidth: 1, borderColor: 'rgba(139,92,246,0.2)',
  },
  statusText: { color: '#a78bfa', fontSize: 13 },
  resultCard: {
    marginTop: 16, padding: 16, borderRadius: 12,
    backgroundColor: 'rgba(6,214,160,0.1)',
    borderWidth: 1, borderColor: 'rgba(6,214,160,0.2)',
  },
  resultTitle: { color: '#06d6a0', fontSize: 14, fontWeight: '700', marginBottom: 4 },
  resultUrl: { color: '#94a3b8', fontSize: 12 },
});
