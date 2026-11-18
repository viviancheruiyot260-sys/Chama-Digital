import fs from 'fs';
import path from 'path';
import {defineConfig} from 'vite';

export default defineConfig(() => {
  return {
    plugins: [
      {
        name: 'copy-static-html-assets',
        apply: 'build',
        closeBundle(error?: Error): void {
          if (error) {
            return;
          }
          const distDir = path.resolve(__dirname, 'dist');
          for (const folder of ['css', 'js', 'images']) {
            const srcFolder = path.resolve(__dirname, folder);
            const destFolder = path.resolve(distDir, folder);
            if (fs.existsSync(distDir) && fs.existsSync(srcFolder)) {
              fs.cpSync(srcFolder, destFolder, {recursive: true, force: true});
            }
          }
        },
      },
    ],
    build: {
      rollupOptions: {
        input: {
          main: path.resolve(__dirname, 'index.html'),
          login: path.resolve(__dirname, 'login.html'),
          register: path.resolve(__dirname, 'register.html'),
          pending: path.resolve(__dirname, 'pending-approval.html'),
          chairperson: path.resolve(__dirname, 'chairperson-dashboard.html'),
          treasurer: path.resolve(__dirname, 'treasurer-dashboard.html'),
          secretary: path.resolve(__dirname, 'secretary-dashboard.html'),
          member: path.resolve(__dirname, 'member-dashboard.html'),
          chamaMembers: path.resolve(__dirname, 'chama-members.html'),
          paymentHistory: path.resolve(__dirname, 'payment-history.html'),
          memberLoans: path.resolve(__dirname, 'member-loans.html'),
          memberProfile: path.resolve(__dirname, 'member-profile.html'),
        },
      },
    },
    server: {
      hmr: process.env.DISABLE_HMR !== 'true',
      watch: process.env.DISABLE_HMR === 'true' ? null : {},
    },
  };
});
