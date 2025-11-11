import React from 'react';
import { createRoot } from 'react-dom/client';
import { AtlasDashboard } from './components/AtlasDashboard';

const root = createRoot(document.getElementById('root')!);
root.render(<AtlasDashboard />);
