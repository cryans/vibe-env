import React, { useState } from 'react';
import AddModelForm from './AddModelForm';
import ModelList from './ModelList';
import { useAppStore } from '../store/appStore';
import type { ModelConfig } from '../store/appStore';

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
          modelsList={modelsList}
          editingModelId={editingModelId}
          editFormData={editFormData}
          onEditFormDataChange={setEditFormData}
          onEditModel={handleEditModel}
          onUpdateModel={handleUpdateModelAndReset}
          onDeleteModel={deleteModel}
          onSelectModel={selectModel}
          onCancelEdit={handleCancelEdit}
        />
      </div>
    </main>
  );
};

export default ModelsView;
