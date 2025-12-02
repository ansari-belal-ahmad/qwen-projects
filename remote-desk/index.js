// Remote Desk - Node.js Application
const http = require('http');
const url = require('url');
const path = require('path');
const fs = require('fs');

const PORT = process.env.PORT || 3000;

// Simple routing system
const routes = {
  '/': (req, res) => {
    res.writeHead(200, { 'Content-Type': 'text/html' });
    res.end(`
      <!DOCTYPE html>
      <html>
      <head>
        <title>Remote Desk</title>
        <style>
          body { font-family: Arial, sans-serif; margin: 40px; }
          h1 { color: #333; }
        </style>
      </head>
      <body>
        <h1>Welcome to Remote Desk</h1>
        <p>Your remote desktop solution is running!</p>
      </body>
      </html>
    `);
  },
  '/api/status': (req, res) => {
    res.writeHead(200, { 'Content-Type': 'application/json' });
    res.end(JSON.stringify({ status: 'running', timestamp: new Date().toISOString() }));
  }
};

const server = http.createServer((req, res) => {
  const route = routes[url.parse(req.url).pathname];
  
  if (route) {
    route(req, res);
  } else {
    res.writeHead(404, { 'Content-Type': 'text/plain' });
    res.end('Route not found');
  }
});

server.listen(PORT, () => {
  console.log(`Remote Desk server running on port ${PORT}`);
  console.log(`Visit http://localhost:${PORT} to see your app`);
});