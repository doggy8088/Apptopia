import { execFile } from "node:child_process";

export interface ExecResult {
  stdout: string;
  stderr: string;
}

export function runCommand(command: string, args: string[], timeoutMs = 120000): Promise<ExecResult> {
  return new Promise((resolve, reject) => {
    execFile(command, args, { timeout: timeoutMs, maxBuffer: 10 * 1024 * 1024 }, (error, stdout, stderr) => {
      if (error) {
        const wrapped = new Error(`${command} 執行失敗: ${error.message}`);
        (wrapped as any).stdout = stdout;
        (wrapped as any).stderr = stderr;
        return reject(wrapped);
      }
      resolve({ stdout, stderr });
    });
  });
}
