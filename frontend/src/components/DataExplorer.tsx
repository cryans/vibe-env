import React, { useEffect, useRef } from 'react';

const DataExplorer: React.FC = () => {
  const tbodyRef = useRef<HTMLTableSectionElement>(null);

  useEffect(() => {
    // Manually tell htmx to initialize the element once React mounts it
    if (tbodyRef.current) {
      htmx.process(tbodyRef.current);
    }
  }, []);

  return (
    <div className="flex-1 p-4 overflow-auto">
      <h2 className="text-xl font-bold mb-4">Data Explorer</h2>
      <div className="overflow-y-auto h-[calc(100vh-150px)] border rounded">
        <table className="w-full text-sm">
          <thead className="bg-gray-100 sticky top-0">
            <tr>
              <th className="px-4 py-2 border">Series ID</th>
              <th className="px-4 py-2 border">Year</th>
              <th className="px-4 py-2 border">Period</th>
              <th className="px-4 py-2 border">Value</th>
              <th className="px-4 py-2 border">Footnote</th>
            </tr>
          </thead>
          <tbody
            ref={tbodyRef}
            hx-get="/api/data/explorer?limit=50&offset=0"
            hx-trigger="load"
            hx-swap="innerHTML"
          >
            {/* HTMX will load the rows here */}
          </tbody>
        </table>
      </div>
    </div>
  );
};

export default DataExplorer;

