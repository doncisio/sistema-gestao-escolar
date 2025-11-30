# 📱 Plano de Migração para Plataforma Mobile (React Native)

## Visão Geral

Este documento detalha o plano completo para desenvolvimento de uma aplicação mobile nativa do Sistema de Gestão Escolar utilizando **React Native** com **Expo**, compartilhando a mesma API backend (FastAPI) do projeto web.

---

## 📊 Análise de Requisitos Mobile

### Público-Alvo Mobile

1. **Professores**
   - Lançar frequência em sala de aula
   - Consultar lista de alunos
   - Visualizar horários
   - Lançar notas rapidamente

2. **Coordenadores/Diretores**
   - Dashboard com estatísticas
   - Aprovar solicitações
   - Visualizar relatórios
   - Notificações em tempo real

3. **Secretaria**
   - Consultar dados de alunos
   - Verificar situação de matrícula
   - Acesso rápido a informações

4. **Pais/Responsáveis** (futuro)
   - Consultar notas dos filhos
   - Verificar frequência
   - Receber comunicados

### Funcionalidades Prioritárias Mobile

| Funcionalidade | Prioridade | Justificativa |
|----------------|------------|---------------|
| Login/Autenticação | Alta | Segurança |
| Dashboard resumido | Alta | Visão geral rápida |
| Lançamento de frequência | Alta | Uso em sala de aula |
| Consulta de alunos | Alta | Uso frequente |
| Lançamento de notas | Média | Agilidade |
| Visualização de horários | Média | Consulta rápida |
| Notificações push | Média | Comunicação |
| Geração de relatórios | Baixa | Melhor no desktop |
| Cadastro completo | Baixa | Melhor no desktop |

---

## 🏗️ Arquitetura Proposta

### Diagrama de Arquitetura Mobile

```
┌─────────────────────────────────────────────────────────────────────┐
│                    APP MOBILE (React Native/Expo)                    │
├─────────────────────────────────────────────────────────────────────┤
│  React Native 0.73+ │ Expo SDK 51+ │ TypeScript │ NativeWind       │
│  React Navigation │ TanStack Query │ Zustand │ AsyncStorage        │
└─────────────────────────────────────────────────────────────────────┘
                              ↓ HTTPS/REST API
┌─────────────────────────────────────────────────────────────────────┐
│                      BACKEND (FastAPI - Compartilhado)               │
├─────────────────────────────────────────────────────────────────────┤
│  Mesma API do projeto Web │ JWT Auth │ Push Notifications (FCM)     │
└─────────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────────┐
│                        INFRAESTRUTURA                                │
├─────────────────────────────────────────────────────────────────────┤
│     MySQL 8.0+ │ Redis │ Firebase Cloud Messaging │ S3/MinIO        │
└─────────────────────────────────────────────────────────────────────┘
```

### Stack Tecnológico Mobile

| Categoria | Tecnologia | Justificativa |
|-----------|------------|---------------|
| Framework | React Native + Expo | Desenvolvimento rápido, compartilha conhecimento React |
| Linguagem | TypeScript | Type safety, mesma linguagem do web |
| Navegação | React Navigation 6 | Padrão da comunidade |
| Estado Global | Zustand | Leve, simples, TypeScript-first |
| Data Fetching | TanStack Query | Cache, revalidação automática |
| UI Components | NativeWind (Tailwind) | Consistência com web |
| Forms | React Hook Form + Zod | Validação consistente |
| Storage | AsyncStorage + MMKV | Persistência local |
| Push Notifications | Expo Notifications + FCM | Cross-platform |
| Câmera/Scanner | Expo Camera | Leitura de QR Code |
| Biometria | Expo Local Authentication | Login seguro |

---

## 📁 Estrutura de Diretórios

```
mobile/
├── app/                           # Expo Router (file-based routing)
│   ├── (auth)/                    # Grupo de rotas de autenticação
│   │   ├── _layout.tsx
│   │   ├── login.tsx
│   │   └── forgot-password.tsx
│   │
│   ├── (tabs)/                    # Grupo de tabs principais
│   │   ├── _layout.tsx            # Tab Navigator
│   │   ├── index.tsx              # Dashboard (Home)
│   │   ├── alunos/
│   │   │   ├── index.tsx          # Lista de alunos
│   │   │   └── [id].tsx           # Detalhes do aluno
│   │   ├── frequencia/
│   │   │   ├── index.tsx          # Seleção de turma
│   │   │   └── lancar.tsx         # Lançamento
│   │   ├── notas/
│   │   │   ├── index.tsx
│   │   │   └── lancar.tsx
│   │   └── perfil/
│   │       └── index.tsx
│   │
│   ├── _layout.tsx                # Root layout
│   └── +not-found.tsx
│
├── src/
│   ├── api/                       # Comunicação com backend
│   │   ├── client.ts              # Axios configurado
│   │   ├── endpoints/
│   │   │   ├── alunos.ts
│   │   │   ├── turmas.ts
│   │   │   ├── frequencia.ts
│   │   │   ├── notas.ts
│   │   │   ├── dashboard.ts
│   │   │   └── auth.ts
│   │   └── index.ts
│   │
│   ├── components/
│   │   ├── ui/                    # Componentes base
│   │   │   ├── Button.tsx
│   │   │   ├── Input.tsx
│   │   │   ├── Card.tsx
│   │   │   ├── Avatar.tsx
│   │   │   ├── Badge.tsx
│   │   │   ├── Spinner.tsx
│   │   │   ├── Modal.tsx
│   │   │   └── Toast.tsx
│   │   │
│   │   ├── common/
│   │   │   ├── Header.tsx
│   │   │   ├── TabBar.tsx
│   │   │   ├── SearchBar.tsx
│   │   │   ├── EmptyState.tsx
│   │   │   ├── ErrorView.tsx
│   │   │   ├── LoadingView.tsx
│   │   │   └── PullToRefresh.tsx
│   │   │
│   │   ├── alunos/
│   │   │   ├── AlunoCard.tsx
│   │   │   ├── AlunoListItem.tsx
│   │   │   └── AlunoDetails.tsx
│   │   │
│   │   ├── frequencia/
│   │   │   ├── TurmaSelector.tsx
│   │   │   ├── FrequenciaList.tsx
│   │   │   └── FrequenciaItem.tsx
│   │   │
│   │   ├── notas/
│   │   │   ├── NotaCard.tsx
│   │   │   ├── NotaInput.tsx
│   │   │   └── NotaList.tsx
│   │   │
│   │   └── dashboard/
│   │       ├── StatCard.tsx
│   │       ├── QuickActions.tsx
│   │       └── RecentActivity.tsx
│   │
│   ├── hooks/
│   │   ├── useAuth.ts
│   │   ├── useAlunos.ts
│   │   ├── useFrequencia.ts
│   │   ├── useNotas.ts
│   │   ├── useDashboard.ts
│   │   ├── useBiometrics.ts
│   │   ├── useNotifications.ts
│   │   ├── useOffline.ts
│   │   └── useDebounce.ts
│   │
│   ├── store/
│   │   ├── authStore.ts
│   │   ├── uiStore.ts
│   │   ├── offlineStore.ts
│   │   └── index.ts
│   │
│   ├── services/
│   │   ├── storage.ts             # AsyncStorage/MMKV wrapper
│   │   ├── notifications.ts       # Push notifications
│   │   ├── biometrics.ts          # Face ID/Touch ID
│   │   └── offline.ts             # Sync offline
│   │
│   ├── utils/
│   │   ├── formatters.ts
│   │   ├── validators.ts
│   │   ├── constants.ts
│   │   └── helpers.ts
│   │
│   ├── types/
│   │   ├── aluno.ts
│   │   ├── turma.ts
│   │   ├── frequencia.ts
│   │   ├── nota.ts
│   │   ├── user.ts
│   │   └── navigation.ts
│   │
│   └── theme/
│       ├── colors.ts
│       ├── typography.ts
│       ├── spacing.ts
│       └── index.ts
│
├── assets/
│   ├── images/
│   │   ├── logo.png
│   │   ├── icon.png
│   │   ├── splash.png
│   │   └── adaptive-icon.png
│   └── fonts/
│
├── app.json                       # Expo config
├── eas.json                       # EAS Build config
├── babel.config.js
├── metro.config.js
├── tailwind.config.js
├── tsconfig.json
├── package.json
└── README.md
```

---

## 🔄 Mapeamento de Telas

### Fluxo de Navegação

```
                    ┌──────────────┐
                    │   Splash     │
                    │   Screen     │
                    └──────┬───────┘
                           │
              ┌────────────┴────────────┐
              │                         │
      ┌───────▼───────┐        ┌───────▼───────┐
      │   Login       │        │   Home        │
      │   (Auth)      │        │   (Tabs)      │
      └───────┬───────┘        └───────┬───────┘
              │                        │
              └────────────┬───────────┘
                           │
        ┌──────────────────┼──────────────────┐
        │                  │                  │
┌───────▼───────┐  ┌───────▼───────┐  ┌───────▼───────┐
│  Dashboard    │  │   Alunos      │  │  Frequência   │
│  (Tab 1)      │  │   (Tab 2)     │  │  (Tab 3)      │
└───────────────┘  └───────┬───────┘  └───────┬───────┘
                           │                  │
                   ┌───────▼───────┐  ┌───────▼───────┐
                   │  Detalhes     │  │   Lançar      │
                   │  Aluno        │  │   Frequência  │
                   └───────────────┘  └───────────────┘
```

### Comparativo de Telas Tkinter vs Mobile

| Tela Tkinter | Tela Mobile | Adaptação |
|--------------|-------------|-----------|
| Janela Principal | Tab Navigator | Dividir em tabs |
| Frame Logo/Header | App Header | StatusBar + Logo |
| Frame Tabela | FlatList | Lista scrollable |
| Frame Detalhes | Screen Detalhes | Navegação stack |
| Toplevel (Modal) | Modal/Bottom Sheet | Componente nativo |
| messagebox | Toast/Alert | Feedback nativo |
| Entry/Combobox | TextInput/Picker | Input nativo |
| DateEntry | DateTimePicker | Seletor nativo |
| Button | Pressable/TouchableOpacity | Botão tappable |

---

## 📋 Cronograma de Implementação

### Fase 1: Setup e Infraestrutura (1-2 semanas)

#### Semana 1: Configuração do Projeto
- [ ] Criar projeto Expo com TypeScript
- [ ] Configurar Expo Router (navegação)
- [ ] Configurar NativeWind (Tailwind)
- [ ] Configurar TanStack Query
- [ ] Configurar Zustand
- [ ] Criar tema base (cores, tipografia)
- [ ] Configurar cliente API (Axios)

#### Semana 2: Autenticação
- [ ] Implementar tela de Login
- [ ] Configurar JWT storage (SecureStore)
- [ ] Implementar refresh token
- [ ] Adicionar biometria (Face ID/Touch ID)
- [ ] Proteção de rotas autenticadas
- [ ] Testes de autenticação

### Fase 2: Funcionalidades Core (3-4 semanas)

#### Semana 3: Dashboard
- [ ] Criar layout de Dashboard
- [ ] Implementar cards de estatísticas
- [ ] Adicionar ações rápidas
- [ ] Implementar pull-to-refresh
- [ ] Integrar com API de estatísticas

#### Semana 4: Módulo Alunos
- [ ] Lista de alunos com busca
- [ ] Filtros por turma/status
- [ ] Detalhes do aluno
- [ ] Swipe actions (ligar, email)
- [ ] Foto do aluno (cache)

#### Semana 5: Lançamento de Frequência
- [ ] Seleção de turma/data
- [ ] Lista de alunos da turma
- [ ] Toggle presença/falta
- [ ] Observações
- [ ] Salvamento em lote
- [ ] Confirmação visual

#### Semana 6: Lançamento de Notas
- [ ] Seleção de turma/disciplina/bimestre
- [ ] Lista de alunos com notas
- [ ] Input numérico otimizado
- [ ] Validação de valores
- [ ] Salvamento em lote

### Fase 3: Funcionalidades Avançadas (2-3 semanas)

#### Semana 7: Offline First
- [ ] Configurar persistência offline
- [ ] Queue de operações pendentes
- [ ] Sync automático ao reconectar
- [ ] Indicador de status offline
- [ ] Conflitos de dados

#### Semana 8: Push Notifications
- [ ] Configurar Expo Notifications
- [ ] Integrar com Firebase Cloud Messaging
- [ ] Notificações de lembretes
- [ ] Deep linking
- [ ] Badges e sons

#### Semana 9: Polimento
- [ ] Animações e transições
- [ ] Loading states
- [ ] Error handling
- [ ] Haptic feedback
- [ ] Acessibilidade
- [ ] Testes E2E

### Fase 4: Publicação (1-2 semanas)

#### Semana 10: Build e Testes
- [ ] Configurar EAS Build
- [ ] Build iOS (TestFlight)
- [ ] Build Android (Internal Testing)
- [ ] Testes em dispositivos reais
- [ ] Correção de bugs

#### Semana 11: Publicação
- [ ] Preparar assets (ícones, screenshots)
- [ ] Criar listagens nas lojas
- [ ] Submeter para revisão
- [ ] Publicação final
- [ ] Monitoramento inicial

---

## 💻 Detalhamento Técnico

### Configuração do Projeto

```json
// app.json
{
  "expo": {
    "name": "Gestão Escolar",
    "slug": "gestao-escolar",
    "version": "1.0.0",
    "orientation": "portrait",
    "icon": "./assets/images/icon.png",
    "scheme": "gestaoescolar",
    "userInterfaceStyle": "automatic",
    "splash": {
      "image": "./assets/images/splash.png",
      "resizeMode": "contain",
      "backgroundColor": "#003A70"
    },
    "assetBundlePatterns": ["**/*"],
    "ios": {
      "supportsTablet": true,
      "bundleIdentifier": "br.com.escola.gestao",
      "infoPlist": {
        "NSFaceIDUsageDescription": "Usar Face ID para login seguro"
      }
    },
    "android": {
      "adaptiveIcon": {
        "foregroundImage": "./assets/images/adaptive-icon.png",
        "backgroundColor": "#003A70"
      },
      "package": "br.com.escola.gestao",
      "permissions": [
        "android.permission.USE_BIOMETRIC"
      ]
    },
    "plugins": [
      "expo-router",
      "expo-secure-store",
      "expo-local-authentication",
      [
        "expo-notifications",
        {
          "icon": "./assets/images/notification-icon.png",
          "color": "#003A70"
        }
      ]
    ],
    "experiments": {
      "typedRoutes": true
    }
  }
}
```

### Exemplo: Tela de Dashboard

```tsx
// app/(tabs)/index.tsx
import { View, ScrollView, RefreshControl } from 'react-native'
import { useCallback, useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { SafeAreaView } from 'react-native-safe-area-context'
import { StatCard } from '@/components/dashboard/StatCard'
import { QuickActions } from '@/components/dashboard/QuickActions'
import { RecentActivity } from '@/components/dashboard/RecentActivity'
import { LoadingView } from '@/components/common/LoadingView'
import { ErrorView } from '@/components/common/ErrorView'
import { dashboardApi } from '@/api/endpoints/dashboard'
import { useAuth } from '@/hooks/useAuth'

export default function DashboardScreen() {
  const { user } = useAuth()
  const [refreshing, setRefreshing] = useState(false)
  
  const { data, isLoading, error, refetch } = useQuery({
    queryKey: ['dashboard', 'stats'],
    queryFn: dashboardApi.getStats,
    staleTime: 1000 * 60 * 5, // 5 minutos
  })
  
  const onRefresh = useCallback(async () => {
    setRefreshing(true)
    await refetch()
    setRefreshing(false)
  }, [refetch])
  
  if (isLoading) return <LoadingView />
  if (error) return <ErrorView message="Erro ao carregar dashboard" onRetry={refetch} />
  
  return (
    <SafeAreaView className="flex-1 bg-gray-50">
      <ScrollView
        className="flex-1 p-4"
        refreshControl={
          <RefreshControl
            refreshing={refreshing}
            onRefresh={onRefresh}
            colors={['#003A70']}
            tintColor="#003A70"
          />
        }
      >
        {/* Saudação */}
        <View className="mb-6">
          <Text className="text-gray-500 text-sm">Bem-vindo,</Text>
          <Text className="text-gray-900 text-xl font-bold">{user?.nome}</Text>
        </View>
        
        {/* Cards de Estatísticas */}
        <View className="flex-row flex-wrap justify-between mb-6">
          <StatCard
            title="Alunos"
            value={data?.totalAlunos || 0}
            icon="people"
            color="#003A70"
          />
          <StatCard
            title="Turmas"
            value={data?.totalTurmas || 0}
            icon="school"
            color="#77B341"
          />
          <StatCard
            title="Frequência Hoje"
            value={`${data?.frequenciaHoje || 0}%`}
            icon="calendar"
            color="#F59E0B"
          />
          <StatCard
            title="Pendências"
            value={data?.pendencias || 0}
            icon="alert-circle"
            color="#EF4444"
          />
        </View>
        
        {/* Ações Rápidas */}
        <QuickActions />
        
        {/* Atividade Recente */}
        <RecentActivity items={data?.recentActivity || []} />
      </ScrollView>
    </SafeAreaView>
  )
}
```

### Exemplo: Lançamento de Frequência

```tsx
// app/(tabs)/frequencia/lancar.tsx
import { useState, useCallback } from 'react'
import { View, Text, FlatList, Alert } from 'react-native'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { useLocalSearchParams, router } from 'expo-router'
import { SafeAreaView } from 'react-native-safe-area-context'
import { FrequenciaItem } from '@/components/frequencia/FrequenciaItem'
import { Button } from '@/components/ui/Button'
import { LoadingView } from '@/components/common/LoadingView'
import { frequenciaApi } from '@/api/endpoints/frequencia'
import { alunosApi } from '@/api/endpoints/alunos'
import * as Haptics from 'expo-haptics'

interface FrequenciaState {
  [alunoId: number]: {
    presente: boolean
    observacao?: string
  }
}

export default function LancarFrequenciaScreen() {
  const { turmaId, data } = useLocalSearchParams<{ turmaId: string; data: string }>()
  const queryClient = useQueryClient()
  
  const [frequencias, setFrequencias] = useState<FrequenciaState>({})
  
  // Buscar alunos da turma
  const { data: alunos, isLoading } = useQuery({
    queryKey: ['alunos', 'turma', turmaId],
    queryFn: () => alunosApi.listarPorTurma(Number(turmaId)),
  })
  
  // Mutation para salvar frequência
  const saveMutation = useMutation({
    mutationFn: (data: FrequenciaState) => 
      frequenciaApi.lancarEmLote({
        turma_id: Number(turmaId),
        data: data,
        frequencias: Object.entries(data).map(([alunoId, freq]) => ({
          aluno_id: Number(alunoId),
          presente: freq.presente,
          observacao: freq.observacao,
        })),
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['frequencia'] })
      queryClient.invalidateQueries({ queryKey: ['dashboard'] })
      Haptics.notificationAsync(Haptics.NotificationFeedbackType.Success)
      Alert.alert('Sucesso', 'Frequência salva com sucesso!', [
        { text: 'OK', onPress: () => router.back() }
      ])
    },
    onError: (error) => {
      Haptics.notificationAsync(Haptics.NotificationFeedbackType.Error)
      Alert.alert('Erro', 'Não foi possível salvar a frequência.')
    },
  })
  
  // Toggle presença
  const togglePresenca = useCallback((alunoId: number) => {
    Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Light)
    setFrequencias(prev => ({
      ...prev,
      [alunoId]: {
        ...prev[alunoId],
        presente: !prev[alunoId]?.presente,
      },
    }))
  }, [])
  
  // Marcar todos como presentes
  const marcarTodosPresentes = useCallback(() => {
    if (!alunos) return
    Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Medium)
    const newState: FrequenciaState = {}
    alunos.forEach(aluno => {
      newState[aluno.id] = { presente: true }
    })
    setFrequencias(newState)
  }, [alunos])
  
  // Salvar frequência
  const handleSalvar = useCallback(() => {
    if (Object.keys(frequencias).length === 0) {
      Alert.alert('Atenção', 'Nenhuma frequência foi marcada.')
      return
    }
    saveMutation.mutate(frequencias)
  }, [frequencias, saveMutation])
  
  if (isLoading) return <LoadingView />
  
  const totalPresentes = Object.values(frequencias).filter(f => f.presente).length
  const totalAusentes = (alunos?.length || 0) - totalPresentes
  
  return (
    <SafeAreaView className="flex-1 bg-white">
      {/* Header com resumo */}
      <View className="bg-primary-500 p-4">
        <Text className="text-white font-bold text-lg">Lançamento de Frequência</Text>
        <Text className="text-white/80 text-sm">Data: {data}</Text>
        <View className="flex-row mt-2">
          <View className="bg-green-500 px-3 py-1 rounded-full mr-2">
            <Text className="text-white text-sm">Presentes: {totalPresentes}</Text>
          </View>
          <View className="bg-red-500 px-3 py-1 rounded-full">
            <Text className="text-white text-sm">Ausentes: {totalAusentes}</Text>
          </View>
        </View>
      </View>
      
      {/* Ação rápida */}
      <View className="p-4 border-b border-gray-200">
        <Button
          variant="outline"
          onPress={marcarTodosPresentes}
          title="Marcar todos como presentes"
        />
      </View>
      
      {/* Lista de alunos */}
      <FlatList
        data={alunos}
        keyExtractor={(item) => item.id.toString()}
        renderItem={({ item }) => (
          <FrequenciaItem
            aluno={item}
            presente={frequencias[item.id]?.presente ?? false}
            onToggle={() => togglePresenca(item.id)}
            onObservacao={(obs) => setFrequencias(prev => ({
              ...prev,
              [item.id]: { ...prev[item.id], observacao: obs }
            }))}
          />
        )}
        contentContainerStyle={{ paddingBottom: 100 }}
      />
      
      {/* Botão Salvar (fixo no rodapé) */}
      <View className="absolute bottom-0 left-0 right-0 p-4 bg-white border-t border-gray-200">
        <Button
          title="Salvar Frequência"
          onPress={handleSalvar}
          loading={saveMutation.isPending}
          disabled={saveMutation.isPending}
        />
      </View>
    </SafeAreaView>
  )
}
```

### Exemplo: Componente FrequenciaItem

```tsx
// src/components/frequencia/FrequenciaItem.tsx
import { View, Text, Pressable, TextInput } from 'react-native'
import { useState } from 'react'
import { Ionicons } from '@expo/vector-icons'
import { Avatar } from '@/components/ui/Avatar'
import type { Aluno } from '@/types/aluno'

interface FrequenciaItemProps {
  aluno: Aluno
  presente: boolean
  onToggle: () => void
  onObservacao: (obs: string) => void
}

export function FrequenciaItem({ 
  aluno, 
  presente, 
  onToggle, 
  onObservacao 
}: FrequenciaItemProps) {
  const [showObs, setShowObs] = useState(false)
  
  return (
    <View className="border-b border-gray-100">
      <Pressable
        className="flex-row items-center p-4 active:bg-gray-50"
        onPress={onToggle}
      >
        {/* Avatar */}
        <Avatar
          name={aluno.nome}
          imageUrl={aluno.foto}
          size={48}
        />
        
        {/* Info do aluno */}
        <View className="flex-1 ml-3">
          <Text className="text-gray-900 font-medium">{aluno.nome}</Text>
          <Text className="text-gray-500 text-sm">Nº {aluno.numero_chamada}</Text>
        </View>
        
        {/* Toggle presença */}
        <View className={`
          w-12 h-12 rounded-full items-center justify-center
          ${presente ? 'bg-green-500' : 'bg-red-500'}
        `}>
          <Ionicons
            name={presente ? 'checkmark' : 'close'}
            size={24}
            color="white"
          />
        </View>
        
        {/* Botão observação */}
        <Pressable
          className="ml-2 p-2"
          onPress={() => setShowObs(!showObs)}
        >
          <Ionicons
            name="chatbubble-outline"
            size={20}
            color="#6B7280"
          />
        </Pressable>
      </Pressable>
      
      {/* Campo de observação (expandível) */}
      {showObs && (
        <View className="px-4 pb-4">
          <TextInput
            className="border border-gray-300 rounded-lg p-3 text-gray-900"
            placeholder="Observação (opcional)"
            multiline
            numberOfLines={2}
            onChangeText={onObservacao}
          />
        </View>
      )}
    </View>
  )
}
```

### Configuração Offline First

```typescript
// src/services/offline.ts
import AsyncStorage from '@react-native-async-storage/async-storage'
import NetInfo from '@react-native-community/netinfo'
import { useQueryClient } from '@tanstack/react-query'

interface QueuedOperation {
  id: string
  type: 'CREATE' | 'UPDATE' | 'DELETE'
  endpoint: string
  data: any
  timestamp: number
}

class OfflineService {
  private static QUEUE_KEY = '@offline_queue'
  
  // Adicionar operação à fila
  async queueOperation(operation: Omit<QueuedOperation, 'id' | 'timestamp'>) {
    const queue = await this.getQueue()
    const newOp: QueuedOperation = {
      ...operation,
      id: crypto.randomUUID(),
      timestamp: Date.now(),
    }
    queue.push(newOp)
    await AsyncStorage.setItem(this.QUEUE_KEY, JSON.stringify(queue))
  }
  
  // Obter fila de operações
  async getQueue(): Promise<QueuedOperation[]> {
    const data = await AsyncStorage.getItem(this.QUEUE_KEY)
    return data ? JSON.parse(data) : []
  }
  
  // Processar fila quando online
  async processQueue(apiClient: any) {
    const queue = await this.getQueue()
    const failed: QueuedOperation[] = []
    
    for (const op of queue) {
      try {
        switch (op.type) {
          case 'CREATE':
            await apiClient.post(op.endpoint, op.data)
            break
          case 'UPDATE':
            await apiClient.put(op.endpoint, op.data)
            break
          case 'DELETE':
            await apiClient.delete(op.endpoint)
            break
        }
      } catch (error) {
        failed.push(op)
      }
    }
    
    // Manter apenas operações que falharam
    await AsyncStorage.setItem(this.QUEUE_KEY, JSON.stringify(failed))
    return queue.length - failed.length // Operações sincronizadas
  }
  
  // Limpar fila
  async clearQueue() {
    await AsyncStorage.removeItem(this.QUEUE_KEY)
  }
}

export const offlineService = new OfflineService()

// Hook para usar offline
export function useOfflineSync() {
  const [isOnline, setIsOnline] = useState(true)
  const [pendingCount, setPendingCount] = useState(0)
  
  useEffect(() => {
    const unsubscribe = NetInfo.addEventListener(state => {
      const wasOffline = !isOnline
      setIsOnline(state.isConnected ?? false)
      
      // Sincronizar quando voltar online
      if (wasOffline && state.isConnected) {
        syncPendingOperations()
      }
    })
    
    // Contar operações pendentes
    loadPendingCount()
    
    return () => unsubscribe()
  }, [])
  
  const loadPendingCount = async () => {
    const queue = await offlineService.getQueue()
    setPendingCount(queue.length)
  }
  
  const syncPendingOperations = async () => {
    const synced = await offlineService.processQueue(apiClient)
    await loadPendingCount()
    return synced
  }
  
  return { isOnline, pendingCount, syncPendingOperations }
}
```

---

## 🔐 Segurança Mobile

### Armazenamento Seguro

```typescript
// src/services/storage.ts
import * as SecureStore from 'expo-secure-store'
import AsyncStorage from '@react-native-async-storage/async-storage'

// Dados sensíveis -> SecureStore
export const secureStorage = {
  async set(key: string, value: string) {
    await SecureStore.setItemAsync(key, value)
  },
  
  async get(key: string) {
    return SecureStore.getItemAsync(key)
  },
  
  async remove(key: string) {
    await SecureStore.deleteItemAsync(key)
  },
}

// Dados não sensíveis -> AsyncStorage
export const storage = {
  async set(key: string, value: any) {
    await AsyncStorage.setItem(key, JSON.stringify(value))
  },
  
  async get<T>(key: string): Promise<T | null> {
    const data = await AsyncStorage.getItem(key)
    return data ? JSON.parse(data) : null
  },
  
  async remove(key: string) {
    await AsyncStorage.removeItem(key)
  },
}
```

### Biometria

```typescript
// src/services/biometrics.ts
import * as LocalAuthentication from 'expo-local-authentication'

export const biometrics = {
  async isAvailable() {
    const hasHardware = await LocalAuthentication.hasHardwareAsync()
    const isEnrolled = await LocalAuthentication.isEnrolledAsync()
    return hasHardware && isEnrolled
  },
  
  async getSupportedTypes() {
    return LocalAuthentication.supportedAuthenticationTypesAsync()
  },
  
  async authenticate(message = 'Confirme sua identidade') {
    const result = await LocalAuthentication.authenticateAsync({
      promptMessage: message,
      fallbackLabel: 'Usar senha',
      disableDeviceFallback: false,
    })
    return result.success
  },
}

// Hook
export function useBiometrics() {
  const [available, setAvailable] = useState(false)
  const [type, setType] = useState<string | null>(null)
  
  useEffect(() => {
    checkBiometrics()
  }, [])
  
  const checkBiometrics = async () => {
    const isAvailable = await biometrics.isAvailable()
    setAvailable(isAvailable)
    
    if (isAvailable) {
      const types = await biometrics.getSupportedTypes()
      if (types.includes(LocalAuthentication.AuthenticationType.FACIAL_RECOGNITION)) {
        setType('Face ID')
      } else if (types.includes(LocalAuthentication.AuthenticationType.FINGERPRINT)) {
        setType('Touch ID')
      }
    }
  }
  
  return { available, type, authenticate: biometrics.authenticate }
}
```

---

## 📱 Build e Publicação

### Configuração EAS Build

```json
// eas.json
{
  "cli": {
    "version": ">= 5.0.0"
  },
  "build": {
    "development": {
      "developmentClient": true,
      "distribution": "internal",
      "ios": {
        "simulator": true
      }
    },
    "preview": {
      "distribution": "internal",
      "ios": {
        "simulator": false
      },
      "android": {
        "buildType": "apk"
      }
    },
    "production": {
      "distribution": "store",
      "ios": {
        "resourceClass": "m1-medium"
      },
      "android": {
        "buildType": "app-bundle"
      }
    }
  },
  "submit": {
    "production": {
      "ios": {
        "appleId": "developer@escola.com.br",
        "ascAppId": "1234567890"
      },
      "android": {
        "serviceAccountKeyPath": "./play-store-key.json",
        "track": "internal"
      }
    }
  }
}
```

### Scripts de Build

```json
// package.json (scripts)
{
  "scripts": {
    "start": "expo start",
    "android": "expo run:android",
    "ios": "expo run:ios",
    "build:preview": "eas build --profile preview",
    "build:prod": "eas build --profile production",
    "submit:ios": "eas submit --platform ios",
    "submit:android": "eas submit --platform android",
    "update": "eas update --auto"
  }
}
```

---

## 📊 Métricas de Sucesso

| Métrica | Meta |
|---------|------|
| Tempo de download do app | < 50MB |
| Tempo de inicialização | < 2s |
| Crash rate | < 1% |
| ANR rate (Android) | < 0.5% |
| Avaliação nas lojas | > 4.0 ⭐ |
| Taxa de retenção D7 | > 40% |
| Latência de API | < 200ms |
| Modo offline funcional | Sim |

---

## 💰 Estimativa de Custos

### Desenvolvimento
- **Desenvolvedor Mobile**: 10-11 semanas
- **Custo estimado**: R$ 35.000 - R$ 50.000

### Custos Recorrentes

| Item | Custo |
|------|-------|
| Apple Developer Program | $99/ano (~R$ 500) |
| Google Play Console | $25 único |
| Firebase (FCM gratuito) | R$ 0 |
| EAS Build (gratuito tier) | R$ 0 |
| **Total Anual** | **~R$ 500** |

---

## ✅ Checklist de Pré-Requisitos

- [ ] API Backend funcionando (FastAPI)
- [ ] Conta Apple Developer
- [ ] Conta Google Play Console
- [ ] MacOS para builds iOS (ou EAS Build)
- [ ] Dispositivos de teste (iOS + Android)
- [ ] Projeto Firebase configurado
- [ ] Design/UI definido
- [ ] Documentação de requisitos

---

## 📚 Referências

- [React Native Documentation](https://reactnative.dev/)
- [Expo Documentation](https://docs.expo.dev/)
- [React Navigation](https://reactnavigation.org/)
- [TanStack Query](https://tanstack.com/query)
- [NativeWind](https://www.nativewind.dev/)
- [EAS Build](https://docs.expo.dev/build/introduction/)
