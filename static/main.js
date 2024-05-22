// Importation des modules Electron nécessaires
const { app, BrowserWindow, ipcMain, dialog } = require('electron');
const path = require('path');
const { spawn } = require('child_process');

// Variable pour stocker le processus Python
let pythonProcess = null;

// Fonction pour créer la fenêtre principale de l'application
function createWindow() {
  // Création de la fenêtre BrowserWindow avec les dimensions spécifiées
  const mainWindow = new BrowserWindow({
    width: 530,
    height: 745,
    webPreferences: {
      // Préchargement du script 'preload.js' pour exposer des API au processus de rendu
      preload: path.join(__dirname, 'preload.js'),
      // Désactivation de l'intégration Node.js dans le rendu pour des raisons de sécurité
      nodeIntegration: false,
      // Isolation du contexte pour une sécurité renforcée
      contextIsolation: true,
    },
    icon: path.join(__dirname, 'logo', 'logo.png') // Set the window icon
  });

  // Chargement du fichier HTML principal dans la fenêtre
  mainWindow.loadFile(path.join(__dirname, '..', 'templates', 'index.html'));

  // Écouteur d'événements IPC pour la demande d'ouverture de la boîte de dialogue de sauvegarde
  ipcMain.on('show-save-dialog', async (event, options) => {
    const result = await dialog.showSaveDialog(mainWindow, options); // Affiche la boîte de dialogue
    event.reply('save-dialog-result', result); // Renvoie le résultat au processus de rendu
  });

  // Écouteur d'événements IPC pour démarrer le serveur Python Flask
  ipcMain.on('start-python-server', (event) => {
    // Vérifie si le processus Python n'est pas déjà en cours d'exécution
    if (!pythonProcess) {
      const pythonPath = path.join(__dirname, '..', 'env', 'bin', 'python'); // Chemin relatif vers l'environnement Python
      const scriptPath = path.join(__dirname, '..', 'vectore', 'indexing.py'); // Chemin relatif vers le script Python

      // Démarre le script Python en tant que processus enfant
      pythonProcess = spawn(pythonPath, [scriptPath]);
      // Gère les erreurs standard du processus Python (stderr)
      pythonProcess.stderr.on('data', (data) => {
        console.error(`stderr: ${data}`);
      });

      pythonProcess.on('close', (code) => {
        console.log(`Python process exited with code ${code}`);
        pythonProcess = null; // Réinitialise le processus Python à null après la fermeture
      });
    }
    // Informe le processus de rendu que le serveur Python a démarré
    event.reply('python-server-started');
  });
}

// Lorsque Electron est prêt, crée la fenêtre principale
app.whenReady().then(createWindow);

// Gestion de la fermeture de toutes les fenêtres de l'application (sauf sur macOS)
app.on('window-all-closed', () => {
  if (process.platform !== 'darwin') { // Vérifie si la plateforme n'est pas macOS
    app.quit(); // Quitte l'application
  }
});

// Sur macOS, gère la réactivation de l'application (par exemple, en cliquant sur l'icône du dock)
app.on('activate', () => {
  if (BrowserWindow.getAllWindows().length === 0) { // Vérifie s'il n'y a pas de fenêtres ouvertes
    createWindow(); // Crée une nouvelle fenêtre
  }
});

// Fermer le processus Python lorsque l'application se ferme
app.on('before-quit', () => {
  if (pythonProcess) {
    pythonProcess.kill(); // Tue le processus Python
  }
});
