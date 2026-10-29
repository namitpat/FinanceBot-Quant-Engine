import { createServer } from 'node:http';

const PORT = 3000;

createServer((_req, res) => {
  res.end('dashboard');
}).listen(PORT);
