import React from 'react';
import { Wrench } from 'lucide-react';
import ModelConfigEditor from './ModelConfigEditor';
import type { ModelConfig } from '../store/appStore'; // Using interface from store

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

const ModelList: React.FC<ModelListProps> = ({
  modelsList,
  editingModelId,
  editFormData,
  onEditFormDataChange,
  onEditModel,
  onUpdateModel,
  onDeleteModel,
  onSelectModel,
  onCancelEdit,
}) => {
  return (
    <div className="space-y-4">
      <h3 className="text-lg font-medium mb-2">Available Models</h3>
      {modelsList.map((m, idx) => (
        <div key={idx} className={`p-4 bg-white border rounded-xl shadow-sm flex flex-col gap-4 ${m.active ? 'border-blue-500 ring-1 ring-blue-500' : ''}`}>
          {editingModelId === m.model_id ? (
            <ModelConfigEditor
              model={m}
              editFormData={editFormData}
              onEditFormDataChange={onEditFormDataChange}
              onCancelEdit={onCancelEdit}
              onSaveEdit={onUpdateModel}
            />
          ) : (
            <div className="flex items-center justify-between">
              <div>
                <div className="font-semibold text-gray-800 flex items-center gap-2">
                  {m.model_name}
                  {m.active && <span className="text-xs bg-blue-100 text-blue-700 px-2 py-0.5 rounded-full font-medium">Active</span>}
                </div>
                <div className="font-mono text-sm text-gray-500">{m.model_id}</div>
                {m.log_path && (
                  <div className="text-xs text-gray-400 mt-1">Logging to: {m.log_path}</div>
                )}
                {m.custom && Object.keys(m.custom).length > 0 && (
                  <div className="mt-3">
                    <div className="text-xs text-gray-500 font-medium mb-1.5 flex items-center gap-1">
                      <Wrench className="w-3 h-3" /> Custom Configuration
                    </div>
                    <ul className="space-y-1">
                      {Object.entries(m.custom).map(([key, value], i) => (
                        <li key={i} className="text-xs flex items-baseline gap-2">
                          <span className="font-semibold text-gray-600 bg-gray-100 px-1.5 py-0.5 rounded">{key}</span>
                          <span className="text-gray-700">{String(value)}</span>
                        </li>
                      ))}
                    </ul>
                  </div>
                )}
              </div>
              <div className="flex flex-wrap items-center gap-2">
                <button
                  onClick={() => onEditModel(m.model_id, { model_name: m.model_name, log_path: m.log_path || '', custom: m.custom || {} })}
                  className="px-3 py-1 text-sm bg-gray-50 hover:bg-gray-100 text-gray-600 rounded-lg transition-colors border"
                >
                  Edit
                </button>
                {!m.active && (
                  <button
                    onClick={() => onSelectModel(m.model_id)}
                    className="px-3 py-1 text-sm bg-gray-100 hover:bg-gray-200 text-gray-700 rounded-lg transition-colors"
                  >
                    Select
                  </button>
                )}
                <button
                  onClick={() => onDeleteModel(m.model_id)}
                  className="px-3 py-1 text-sm bg-red-50 hover:bg-red-100 text-red-600 rounded-lg transition-colors"
                  title="Delete Model"
                >
                  Delete
                </button>
              </div>
            </div>
          )}
        </div>
      ))}
      {modelsList.length === 0 && <p className="text-gray-500">No models configured.</p>}
    </div>
  );
};

export default ModelList;
