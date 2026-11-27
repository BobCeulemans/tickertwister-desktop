// SPDX-License-Identifier: AGPL-3.0-only
// Copyright ©2026 Bob Ceulemans
import React from 'react';
import {createRoot} from 'react-dom/client';
import {initialPreferences,applyAppearance} from './workspacePreferences.mjs';
import ProfileGate from './ProfileGate.jsx';
import './style.css';
import './mac.css';
// Apply readable colours before the encrypted profile is opened.
applyAppearance(initialPreferences(window.localStorage,window.__ttSystemLanguage||navigator.language,null,'light'),window.matchMedia('(prefers-color-scheme: dark)').matches);
createRoot(document.getElementById('root')).render(<ProfileGate/>);
