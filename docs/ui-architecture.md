# UI Architecture with Zustand

This document outlines the architecture of the frontend application after implementing Zustand for state management. The goal was to centralize global state, reduce prop drilling, and improve maintainability.

## 1. Zustand Store: `frontend/src/store/appStore.ts`

The core of our state management is the `useAppStore` hook, created using Zustand. This store holds all application-wide state and the actions to modify that state. It acts as a single source of truth for global data.

### Key State Variables:

*   `viewMode`: (`ViewMode`) - Controls which main content view is currently displayed (e.g., `'direct_chat'`, `'pidev_sessions'`, `'models'`).
*   `isSidebarOpen`: (`boolean`) - Determines the visibility of the main navigation sidebar.
*   `configuredModel`: (`string`) - The name of the currently active LLM model.
*   `modelsList`: (`ModelConfig[]`) - A list of all configured LLM models.
*   `piDevSessions`: (`SessionInfo[]`) - A list of recorded sessions from the Pi development agent.
*   `directChatSessions`: (`SessionInfo[]`) - A list of saved direct chat conversations with the LLM.
*   `activePiDevSessionDetail`: (`SessionDetailItem[] | null`) - The detailed content of a specific PiDev session being viewed.
*   `currentDirectChatMessages`: (`Message[]`) - The messages for the *currently active* direct chat.
*   `currentDirectChatSessionId`: (`string`) - The unique ID of the *currently active* direct chat.

### Key Actions (Examples):

*   `toggleSidebar()`: Toggles the `isSidebarOpen` state.
*   `setViewMode(mode: ViewMode)`: Changes the `viewMode`.
*   `loadInitialAppData()`: Fetches initial models and session data on application startup.
*   `addDirectChatMessage(role, content)`: Adds a new message to `currentDirectChatMessages`.
*   `loadPiDevSessionDetail(filename)`: Fetches and sets the `activePiDevSessionDetail`.
*   `addModel(model_id, model_name)`: Dispatches API call to add a model and refreshes the `modelsList`.

## 2. Component Interaction with the Store

Components now access the necessary state and actions directly from `useAppStore` instead of receiving them as props from `App.tsx` (or other parent components). This significantly reduces prop drilling.

### Example: Model Management Components

Let's illustrate how the model management components (`ModelsView`, `ModelList`, `ModelConfigEditor`, `AddModelForm`) interact with the Zustand store.

#### `frontend/src/components/ModelsView.tsx`

This component is the entry point for model management. It connects directly to the `useAppStore` to get the `modelsList` and the actions for managing models (`addModel`, `updateModel`, `deleteModel`, `selectModel`). Local UI-specific state (like form input values or which model is being edited) remains within `ModelsView`.

```tsx
// frontend/src/components/ModelsView.tsx
import React, { useState } from 'react';
import AddModelForm from './AddModelForm';
import ModelList from './ModelList';
import { useAppStore, ModelConfig } from '../store/appStore';

const ModelsView: React.FC = () => {
  const {
    modelsList,
    addModel,
    updateModel,
    deleteModel,
    selectModel,
  } = useAppStore();

  const [newModelId, setNewModelId] = useState('');
  const [newModelName, setNewModelName] = useState('');
  const [editingModelId, setEditingModelId] = useState<string | null>(null);
  const [editFormData, setEditFormData] = useState<Partial<ModelConfig>>({});

  const handleAddModelSubmit = () => {
    // Dispatches store action to add a model
    addModel(newModelId, newModelName);
    setNewModelId('');
    setNewModelName('');
  };

  const handleEditModel = (modelId: string, initialData: Partial<ModelConfig>) => {
    setEditingModelId(modelId);
    setEditFormData(initialData);
  };

  const handleCancelEdit = () => {
    setEditingModelId(null);
    setEditFormData({});
  };

  const handleUpdateModelAndReset = async (model_id: string, updatedConfig: Partial<ModelConfig>) => {
    // Dispatches store action to update a model
    await updateModel(model_id, updatedConfig);
    setEditingModelId(null);
    setEditFormData({});
  };

  return (
    <main className="flex-1 overflow-y-auto p-4 md:p-6">
      <div className="max-w-4xl mx-auto">
        <h2 className="text-2xl font-semibold mb-6">Manage Models</h2>
        
        <AddModelForm
          newModelId={newModelId}
          newModelName={newModelName}
          onNewModelIdChange={setNewModelId}
          onNewModelNameChange={setNewModelName}
          onAddModel={handleAddModelSubmit}
        />

        <ModelList
          modelsList={modelsList} // State from store passed as prop
          editingModelId={editingModelId} // Local state passed as prop
          editFormData={editFormData} // Local state passed as prop
          onEditFormDataChange={setEditFormData} // Local state setter passed as prop
          onEditModel={handleEditModel} // Local handler passed as prop
          onUpdateModel={handleUpdateModelAndReset} // Local handler (dispatches store action) passed as prop
          onDeleteModel={deleteModel} // Store action passed as prop
          onSelectModel={selectModel} // Store action passed as prop
          onCancelEdit={handleCancelEdit} // Local handler passed as prop
        />
      </div>
    </main>
  );
};

export default ModelsView;
```

#### `frontend/src/components/ModelList.tsx`

This component receives data (`modelsList`, `editingModelId`, `editFormData`) and action handlers from its parent (`ModelsView`) as props. It does **not** directly connect to the Zustand store, as its concerns are limited to rendering the list and delegating actions back to `ModelsView`.

```tsx
// frontend/src/components/ModelList.tsx (simplified)
import React from 'react';
import ModelConfigEditor from './ModelConfigEditor';
import { ModelConfig } from '../store/appStore'; // Using interface from store

interface ModelListProps {
  modelsList: ModelConfig[];
  editingModelId: string | null;
  editFormData: Partial<ModelConfig>;
  onEditFormDataChange: (data: Partial<ModelConfig>) => void;
  onEditModel: (modelId: string, initialData: Partial<ModelConfig>) => void;
  onUpdateModel: (model_id: string, updatedConfig: Partial<ModelConfig>) => void;
  onDeleteModel: (model_id: string) => void;
  onSelectModel: (model_id: string) => void;
  onCancelEdit: () => void;
}

const ModelList: React.FC<ModelListProps> = (props) => {
  const { modelsList, editingModelId, onEditModel, onDeleteModel, onSelectModel, onUpdateModel, onCancelEdit, editFormData, onEditFormDataChange } = props;

  return (
    <div className="space-y-4">
      {/* ... rendering logic ... */}
      {modelsList.map((m, idx) => (
        <div key={idx} className={`p-4 ${m.active ? 'border-blue-500' : ''}`}>
          {editingModelId === m.model_id ? (
            <ModelConfigEditor
              model={m}
              editFormData={editFormData}
              onEditFormDataChange={onEditFormDataChange}
              onCancelEdit={onCancelEdit}
              onSaveEdit={onUpdateModel} // When saved, it calls `handleUpdateModelAndReset` in `ModelsView`
            />
          ) : (
            <div className="flex items-center justify-between">
              {/* ... display model details ... */}
              <button onClick={() => onEditModel(m.model_id, { model_name: m.model_name, log_path: m.log_path || '', custom: m.custom || {} })}>Edit</button>
              {!m.active && (<button onClick={() => onSelectModel(m.model_id)}>Select</button>)}
              <button onClick={() => onDeleteModel(m.model_id)}>Delete</button> // Dispatches store action via prop
            </div>
          )}
        </div>
      ))}
      {modelsList.length === 0 && <p>No models configured.</p>}
    </div>
  );
};

export default ModelList;
```

This architecture keeps `ModelsView` responsible for orchestrating model-related logic and interacting with the global store, while `ModelList` and its children remain focused on presentation and local editing state, receiving necessary callbacks as props.

### Other Key Component Interactions:

*   **`App.tsx`**: Consumes `viewMode`, `isSidebarOpen`, `configuredModel`, `activePiDevSessionDetail`, `piDevSessions`, `modelsList` and `loadInitialAppData` from the store. It orchestrates the top-level layout and initial data loading.
*   **`Header.tsx`**: Consumes `configuredModel` and `toggleSidebar` from the store.
*   **`Sidebar.tsx`**: Consumes `isSidebarOpen`, `viewMode`, `directChatSessions`, `setViewMode`, `startNewDirectChat`, `loadDirectChatHistory`, `navigateToPiDevSessions`, `refreshModelsConfig` from the store.
*   **`DirectChatContainer.tsx`**: Consumes `currentDirectChatMessages`, `currentDirectChatSessionId`, `addDirectChatMessage`, `addDirectChatSessionToList` from the store. Manages its own local `input` and `isLoading` state, dispatching global actions for messages.
*   **`PiDevSessionsOverview.tsx`**: Consumes `piDevSessions` and `loadPiDevSessionDetail` from the store.
*   **`PiDevSessionDetail.tsx`**: Consumes `activePiDevSessionDetail` and `clearPiDevSessionDetail` from the store.

This new structure leverages Zustand to create a clear separation of concerns, making the application's state flow more predictable and easier to debug.