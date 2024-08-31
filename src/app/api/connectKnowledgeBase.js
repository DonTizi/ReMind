import { exec } from 'child_process';

export default function handler(req, res) {
  if (req.method === 'POST') {
    exec('python swift.py', (error, stdout, stderr) => {
      if (error) {
        return res.status(500).json({ error: error.message });
      }
      if (stderr) {
        return res.status(500).json({ error: stderr });
      }
      res.status(200).json({ message: 'Knowledge base connected', output: stdout });
    });
  } else {
    res.status(405).json({ message: 'Method not allowed' });
  }
}
