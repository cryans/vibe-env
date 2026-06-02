import React from 'react';

interface AddModelFormProps {
  newModelId: string;
  newModelName: string;
  onNewModelIdChange: (value: string) => void;
  onNewModelNameChange: (value: string) => void;
  onAddModel: () => void;
}

const AddModelForm: React.FC<AddModelFormProps> = ({
  newModelId,
  newModelName,
  onNewModelIdChange,
  onNewModelNameChange,
  onAddModel,
}) => {
  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (newModelId && newModelName) {
      onAddModel();
    }
  };

  return (
    <div className="bg-white p-4 border rounded-xl shadow-sm mb-6">
      <h3 className="text-lg font-medium mb-4">Add Model</h3>
      <form onSubmit={handleSubmit} className="flex flex-col sm:flex-row gap-4">
        <input
          type="text"
          placeholder="Model ID (e.g., gemini-1.5-pro)"
          value={newModelId}
          onChange={(e) => onNewModelIdChange(e.target.value)}
          className="flex-1 border rounded-lg px-3 py-2 focus:ring-2 focus:ring-blue-500 outline-none"
          required
        />
        <input
          type="text"
          placeholder="Display Name (e.g., Gemini 1.5 Pro)"
          value={newModelName}
          onChange={(e) => onNewModelNameChange(e.target.value)}
          className="flex-1 border rounded-lg px-3 py-2 focus:ring-2 focus:ring-blue-500 outline-none"
          required
        />
        <button
          type="submit"
          className="bg-blue-600 text-white px-6 py-2 rounded-lg hover:bg-blue-700 transition-colors whitespace-nowrap"
        >
          Add Model
        </button>
      </form>
    </div>
  );
};

export default AddModelForm;
