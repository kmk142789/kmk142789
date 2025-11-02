import { WebSocketServer } from 'ws';

let wss;

function broadcast(payload) {
  if (!wss) {
    return 0;
  }

  const message = JSON.stringify(payload);
  let delivered = 0;
  for (const client of wss.clients) {
    if (client.readyState === client.OPEN) {
      client.send(message);
      delivered += 1;
    }
  }
  return delivered;
}

export const realtimeDashboard = {
  initialize(server) {
    if (wss) {
      return wss;
    }

    wss = new WebSocketServer({ server });
    wss.on('connection', (socket) => {
      socket.send(
        JSON.stringify({
          type: 'welcome',
          message: 'ECHO :: Sovereign Dashboard Link Established',
          timestamp: Date.now(),
        })
      );
    });
    return wss;
  },
  broadcast,
  getClientCount() {
    return wss ? wss.clients.size : 0;
  },
};
