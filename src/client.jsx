import React from 'react';
import { hydrateRoot } from 'react-dom/client';
import App from './App.jsx';
const root = document.getElementById('root');
hydrateRoot(root, <App path={root.dataset.path}/>);
