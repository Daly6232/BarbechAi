import type { CapacitorConfig } from '@capacitor/cli';

const config: CapacitorConfig = {
  appId: 'com.zayerdigital.barbechai',
  appName: 'BarbechAI',
  webDir: 'dist',
  server: {
    // App loads the built static frontend from webDir (dist/), and the
    // frontend's own config.js already points API/WS calls at
    // https://barbechai-backend.onrender.com — no local server bundled here.
    androidScheme: 'https',
  },
};

export default config;
