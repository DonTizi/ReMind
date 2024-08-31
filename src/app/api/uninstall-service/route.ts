import { NextResponse } from 'next/server';
import { exec } from 'child_process';

export async function GET() {
  return new Promise((resolve) => {
    exec('python uninstaller.py', (error, stdout, stderr) => {
      if (error) {
        resolve(NextResponse.json({ message: `Error: ${error.message}` }, { status: 500 }));
        return;
      }
      if (stderr) {
        resolve(NextResponse.json({ message: `Stderr: ${stderr}` }, { status: 500 }));
        return;
      }
      resolve(NextResponse.json({ message: 'Service uninstalled successfully' }));
    });
  });
}
