import React from 'react';
import { Wrench } from 'lucide-react';
import type { ModelConfig } from '../store/appStore';
import { useAppStore } from '../store/appStore';

interface ModelConfigEditorProps {
  model: ModelConfig;
  editFormData: Partial<ModelConfig>;
  onEditFormDataChange: (data: Partial<ModelConfig>) => void;
  onCancelEdit: () => void;
  onSaveEdit: (model_id: string, updatedConfig: Partial<ModelConfig>) => void;
}

const ModelConfigEditor: React.FC<ModelConfigEditorProps> = ({
  model,
  editFormData,
  onEditFormDataChange,
  onCancelEdit,
  onSaveEdit,
}) => {
  const { setAlertMessage } = useAppStore();

  return (
    <div className="flex flex-col gap-3">
      <div className="flex justify-between items-center">
        <span className="font-mono text-sm font-semibold text-gray-700">Editing: {model.model_id}</span>
      </div>
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-1">Display Name</label>
        <input
          type="text"
          className="w-full border rounded-lg px-3 py-2 focus:ring-2 focus:ring-blue-500 outline-none text-sm"
          value={editFormData.model_name || ''}
          onChange={e => onEditFormDataChange({...editFormData, model_name: e.target.value})}
        />
      </div>
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-1">Log Path (JSONL)</label>
        <input
          type="text"
          className="w-full border rounded-lg px-3 py-2 focus:ring-2 focus:ring-blue-500 outline-none text-sm"
          placeholder="e.g. logs/{session_id}.jsonl"
          value={editFormData.log_path || ''}
          onChange={e => onEditFormDataChange({...editFormData, log_path: e.target.value})}
        />
        <p className="text-[10px] text-gray-500 mt-1">Use {"{session_id}"} placeholder for dynamic file naming.</p>
      </div>
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-1">Custom JSON Data</label>
        <textarea
          className="w-full border rounded-lg px-3 py-2 focus:ring-2 focus:ring-blue-500 outline-none text-sm font-mono h-24"
          placeholder='{"is_paid": true}'
          value={
            typeof editFormData.custom === 'string'
              ? editFormData.custom
              : JSON.stringify(editFormData.custom || {}, null, 2)
          }
          onChange={e => {
            onEditFormDataChange({...editFormData, custom: e.target.value as any});
          }}
        />
      </div>
      <div className="flex justify-end gap-2 mt-2">
        <button
          onClick={onCancelEdit}
          className="px-4 py-2 text-sm bg-gray-100 hover:bg-gray-200 text-gray-700 rounded-lg transition-colors"
        >
          Cancel
        </button>
        <button
          onClick={() => {
            let parsedCustom = {};
            try {
              if (typeof editFormData.custom === 'string') {
                parsedCustom = JSON.parse(editFormData.custom);
              } else {
                parsedCustom = editFormData.custom || {};
              }
            } catch (e) {
              setAlertMessage("Invalid JSON in Custom Data");
              return;
            }
            onSaveEdit(model.model_id, {
              model_name: editFormData.model_name || model.model_name,
              log_path: editFormData.log_path || '',
              custom: parsedCustom
            });
          }}
          className="px-4 py-2 text-sm bg-blue-600 hover:bg-blue-700 text-white rounded-lg transition-colors"
        >
          Save Changes
        </button>
      </div>
    </div>
  );
};

export default ModelConfigEditor;
