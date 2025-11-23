export type LogLevel = "info" | "warn" | "error";

export class LogService {
  private lines: string[] = [];

  log(level: LogLevel, msg: string) {
    const line = `[${new Date().toISOString()}] [${level.toUpperCase()}] ${msg}`;
    this.lines.push(line);
    console.log(line);
  }

  getRecent(limit = 50) {
    return this.lines.slice(-limit);
  }
}
