import React from 'react';
import ReactDOM from 'react-dom/client';
import { App } from './App';
import './i18n';
import './assets/styles/index.css';
import './assets/styles/rtl.css';
import './assets/styles/components.css';

window.addEventListener('error', (e) => {
  const div = document.createElement('div');
  div.style.position = 'fixed';
  div.style.top = '0';
  div.style.left = '0';
  div.style.background = 'red';
  div.style.color = 'white';
  div.style.zIndex = '999999';
  div.style.padding = '20px';
  div.innerText = `CRASH: ${e.message} at ${e.filename}:${e.lineno}`;
  document.body.appendChild(div);
});

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
);
