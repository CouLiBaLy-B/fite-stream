/**
 * Settings Screen — Server config, GPU status, about
 */

import React, { useState, useEffect } from 'react';
import { View, Text, TextInput, TouchableOpacity, ScrollView, StyleSheet } from 'react-native';
import FitStreamAPI, { DEFAULT_API } from '../services/api';

export default function SettingsScreen() {
  const [serverUrl, setServerUrl] = useState(DEFAULT_API);
  const [status, setStatus] = useState(null);
  const [checking, setChecking] = useState(false);

  const checkConnection = async () => {
    setChecking(true);
    try {
      const api = new FitStreamAPI(serverUrl);
      const data = await api.getStatus();
      setStatus(data);
    } catch (e) {
      setStatus({ ok: false, error: e.message });
    }
    setChecking(false);
  };

  useEffect(() => { checkConnection(); }, []);

  return (
    <ScrollView style={s.container}>
      <Text style={s.sectionTitle}>Server Connection</Text>
      <TextInput
        style={s.input}
        value={serverUrl}
        onChangeText={setServerUrl}
        placeholder="http://localhost:8000"
        placeholderTextColor="#64748b"
        autoCapitalize="none"
        autoCorrect={false}
      />
      <TouchableOpacity style={s.button} onPress={checkConnection}>
        <Text style={s.buttonText}>
          {checking ? '⏳ Checking...' : '🔄 Test Connection'}
        </Text>
      </TouchableOpacity>

      {status && (
        <View style={[s.statusCard, status.ok ? s.statusOk : s.statusErr]}>
          <Text style={s.statusTitle}>
            {status.ok ? '🟢 Connected' : '🔴 Disconnected'}
          </Text>
          {status.ok && (
            <>
              <Text style={s.statusLine}>GPU: {status.gpu ? '✅ Available' : '❌ None'}</Text>
              {status.gpu_free_gb > 0 && (
                <Text style={s.statusLine}>Free VRAM: {status.gpu_free_gb.toFixed(1)} GB</Text>
              )}
              <Text style={s.statusLine}>Active Jobs: {status.active_jobs}</Text>
            </>
          )}
          {status.error && <Text style={s.statusError}>{status.error}</Text>}
        </View>
      )}

      <Text style={s.sectionTitle}>About</Text>
      <View style={s.aboutCard}>
        <Text style={s.aboutTitle}>🎬 FitStream Mobile</Text>
        <Text style={s.aboutVersion}>v0.1.0</Text>
        <Text style={s.aboutDesc}>
          AI-powered video animation platform.{'\n'}
          Transform photos into living stories.
        </Text>
        <Text style={s.aboutTech}>
          Built with React Native / Expo{'\n'}
          Backend: Wan VACE + LoomVideo{'\n'}
          281 tests passing ✅
        </Text>
      </View>
    </ScrollView>
  );
}

const s = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#07070e', padding: 16 },
  sectionTitle: {
    fontSize: 11, fontWeight: '700', color: '#64748b',
    letterSpacing: 1, marginBottom: 12, marginTop: 20,
  },
  input: {
    backgroundColor: 'rgba(255,255,255,0.03)',
    borderWidth: 1, borderColor: 'rgba(255,255,255,0.08)',
    borderRadius: 12, padding: 14, color: '#f1f5f9', fontSize: 14,
    marginBottom: 12,
  },
  button: {
    backgroundColor: 'rgba(255,255,255,0.06)',
    borderWidth: 1, borderColor: 'rgba(255,255,255,0.1)',
    borderRadius: 12, padding: 14, alignItems: 'center',
  },
  buttonText: { color: '#a78bfa', fontSize: 14, fontWeight: '700' },
  statusCard: {
    marginTop: 16, padding: 16, borderRadius: 12,
    borderWidth: 1,
  },
  statusOk: {
    backgroundColor: 'rgba(6,214,160,0.05)',
    borderColor: 'rgba(6,214,160,0.2)',
  },
  statusErr: {
    backgroundColor: 'rgba(239,68,68,0.05)',
    borderColor: 'rgba(239,68,68,0.2)',
  },
  statusTitle: { color: '#f1f5f9', fontSize: 14, fontWeight: '700', marginBottom: 8 },
  statusLine: { color: '#94a3b8', fontSize: 13, marginBottom: 2 },
  statusError: { color: '#ef4444', fontSize: 12, marginTop: 4 },
  aboutCard: {
    padding: 20, borderRadius: 16,
    backgroundColor: 'rgba(255,255,255,0.03)',
    borderWidth: 1, borderColor: 'rgba(255,255,255,0.06)',
  },
  aboutTitle: { fontSize: 20, fontWeight: '800', color: '#f1f5f9', marginBottom: 4 },
  aboutVersion: { fontSize: 12, color: '#8b5cf6', fontWeight: '600', marginBottom: 12 },
  aboutDesc: { fontSize: 14, color: '#94a3b8', lineHeight: 22, marginBottom: 12 },
  aboutTech: { fontSize: 12, color: '#64748b', lineHeight: 20 },
});
