export type BridgeChannel = "github" | "colab" | "aistudio" | "termux" | "telegram";

export type BridgePing = {
  channel: BridgeChannel;
  payload: string;
  ts: number;
};

export class BridgeLayer {
  private history: BridgePing[] = [];

  record(channel: BridgeChannel, payload: string) {
    const ping: BridgePing = {
      channel,
      payload,
      ts: Date.now()
    };
    this.history.push(ping);
    return ping;
  }

  getHistory(limit = 50): BridgePing[] {
    return this.history.slice(-limit);
  }
}
