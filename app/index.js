const express = require('express');
const app = express();
const PORT = process.env.PORT || 3000;

const BUILD_INFO = {
  version: process.env.APP_VERSION || '1.0.0',
  commit:  process.env.GITHUB_SHA   || 'local',
  builtAt: process.env.BUILD_TIME   || new Date().toISOString(),
};

app.get('/health', (req, res) => {
  res.json({ status: 'ok', timestamp: new Date().toISOString() });
});

app.get('/version', (req, res) => {
  res.json(BUILD_INFO);
});

app.listen(PORT, () => {
  console.log(`Server running on port ${PORT}`);
  console.log(`Version: ${BUILD_INFO.version} | Commit: ${BUILD_INFO.commit}`);
});
