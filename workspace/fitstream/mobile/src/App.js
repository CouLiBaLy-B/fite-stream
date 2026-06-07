/**
 * FitStream Mobile App
 * React Native / Expo entry point
 */

import React from 'react';
import { NavigationContainer } from '@react-navigation/native';
import { createBottomTabNavigator } from '@react-navigation/bottom-tabs';
import { StatusBar } from 'react-native';

import CreateScreen from './screens/CreateScreen';
import GalleryScreen from './screens/GalleryScreen';
import SettingsScreen from './screens/SettingsScreen';

const Tab = createBottomTabNavigator();

export default function App() {
  return (
    <NavigationContainer>
      <StatusBar barStyle="light-content" backgroundColor="#07070e" />
      <Tab.Navigator
        screenOptions={{
          headerStyle: { backgroundColor: '#07070e', borderBottomColor: '#1a1a2e' },
          headerTintColor: '#f1f5f9',
          headerTitleStyle: { fontWeight: '800' },
          tabBarStyle: { backgroundColor: '#07070e', borderTopColor: '#1a1a2e' },
          tabBarActiveTintColor: '#8b5cf6',
          tabBarInactiveTintColor: '#64748b',
        }}
      >
        <Tab.Screen
          name="Create"
          component={CreateScreen}
          options={{
            title: '🎬 Create',
            headerTitle: 'FitStream',
          }}
        />
        <Tab.Screen
          name="Gallery"
          component={GalleryScreen}
          options={{ title: '🖼️ Gallery' }}
        />
        <Tab.Screen
          name="Settings"
          component={SettingsScreen}
          options={{ title: '⚙️ Settings' }}
        />
      </Tab.Navigator>
    </NavigationContainer>
  );
}
