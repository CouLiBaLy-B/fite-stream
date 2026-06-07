/**
 * Gallery Screen — Browse generated videos
 */

import React, { useState, useEffect, useCallback } from 'react';
import {
  View, Text, FlatList, TouchableOpacity,
  RefreshControl, StyleSheet, Dimensions,
} from 'react-native';
import FitStreamAPI from '../services/api';

const api = new FitStreamAPI();
const { width } = Dimensions.get('window');
const CARD_WIDTH = (width - 48) / 2;

export default function GalleryScreen() {
  const [items, setItems] = useState([]);
  const [refreshing, setRefreshing] = useState(false);
  const [page, setPage] = useState(0);
  const [hasMore, setHasMore] = useState(true);

  const load = useCallback(async (p = 0) => {
    try {
      const data = await api.getGallery(p, 12);
      if (p === 0) {
        setItems(data.items || []);
      } else {
        setItems(prev => [...prev, ...(data.items || [])]);
      }
      setHasMore(data.has_next || false);
      setPage(p);
    } catch (e) {
      console.error('Gallery load failed:', e);
    }
  }, []);

  useEffect(() => { load(0); }, []);

  const onRefresh = async () => {
    setRefreshing(true);
    await load(0);
    setRefreshing(false);
  };

  const loadMore = () => {
    if (hasMore) load(page + 1);
  };

  const renderItem = ({ item }) => {
    const icons = { animate: '📸', story: '📖', tryon: '👗', style: '🎭', compose: '🎨' };
    return (
      <TouchableOpacity style={s.card}>
        <View style={s.cardThumb}>
          <Text style={s.cardIcon}>{icons[item.type] || '🎬'}</Text>
        </View>
        <View style={s.cardBody}>
          <Text style={s.cardType}>{(item.type || 'animate').toUpperCase()}</Text>
          <Text style={s.cardPrompt} numberOfLines={2}>{item.prompt || ''}</Text>
        </View>
      </TouchableOpacity>
    );
  };

  return (
    <View style={s.container}>
      {items.length === 0 ? (
        <View style={s.empty}>
          <Text style={s.emptyIcon}>🖼️</Text>
          <Text style={s.emptyText}>No videos yet</Text>
          <Text style={s.emptySubtext}>Create your first animation!</Text>
        </View>
      ) : (
        <FlatList
          data={items}
          renderItem={renderItem}
          keyExtractor={(item, i) => item.id || `${i}`}
          numColumns={2}
          columnWrapperStyle={s.row}
          contentContainerStyle={s.grid}
          refreshControl={
            <RefreshControl refreshing={refreshing} onRefresh={onRefresh}
              tintColor="#8b5cf6" />
          }
          onEndReached={loadMore}
          onEndReachedThreshold={0.5}
        />
      )}
    </View>
  );
}

const s = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#07070e' },
  grid: { padding: 16 },
  row: { justifyContent: 'space-between', marginBottom: 12 },
  card: {
    width: CARD_WIDTH, borderRadius: 16, overflow: 'hidden',
    backgroundColor: 'rgba(255,255,255,0.04)',
    borderWidth: 1, borderColor: 'rgba(255,255,255,0.08)',
  },
  cardThumb: {
    height: 120, alignItems: 'center', justifyContent: 'center',
    backgroundColor: 'rgba(139,92,246,0.05)',
  },
  cardIcon: { fontSize: 36 },
  cardBody: { padding: 10 },
  cardType: { fontSize: 9, fontWeight: '700', color: '#8b5cf6', letterSpacing: 1, marginBottom: 4 },
  cardPrompt: { fontSize: 12, color: '#94a3b8', lineHeight: 16 },
  empty: { flex: 1, alignItems: 'center', justifyContent: 'center' },
  emptyIcon: { fontSize: 48, marginBottom: 12, opacity: 0.4 },
  emptyText: { color: '#94a3b8', fontSize: 16, fontWeight: '600' },
  emptySubtext: { color: '#64748b', fontSize: 13, marginTop: 4 },
});
