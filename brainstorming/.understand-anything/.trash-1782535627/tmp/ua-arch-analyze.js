const fs = require('fs');
const path = require('path');

const [inputPath, outputPath] = process.argv.slice(2);
const input = JSON.parse(fs.readFileSync(inputPath, 'utf-8'));

const { fileNodes, importEdges, allEdges } = input;

// 1. Compute directory grouping
const dirGroups = {};
for (const node of fileNodes) {
  const dir = path.dirname(node.filePath);
  if (!dirGroups[dir]) dirGroups[dir] = [];
  dirGroups[dir].push(node.id);
}

// 2. Compute node type grouping
const typeGroups = {};
for (const node of fileNodes) {
  if (!typeGroups[node.type]) typeGroups[node.type] = [];
  typeGroups[node.type].push(node.id);
}

// 3. Edge analysis
const edgeTypes = {};
for (const e of allEdges) {
  if (!edgeTypes[e.type]) edgeTypes[e.type] = [];
  edgeTypes[e.type].push(e);
}

// 4. Dependency analysis — count outgoing and incoming edges per node
const outgoing = {};
const incoming = {};
for (const node of fileNodes) {
  outgoing[node.id] = [];
  incoming[node.id] = [];
}
for (const e of allEdges) {
  const source = typeof e.source === 'string' ? e.source : e.source.id;
  const target = typeof e.target === 'string' ? e.target : e.target.id;
  if (outgoing[source]) outgoing[source].push(e);
  if (incoming[target]) incoming[target].push(e);
}

// 5. Most connected nodes
const connectivity = fileNodes.map(n => ({
  id: n.id,
  name: n.name,
  outgoing: (outgoing[n.id] || []).length,
  incoming: (incoming[n.id] || []).length,
  total: (outgoing[n.id] || []).length + (incoming[n.id] || []).length
})).sort((a, b) => b.total - a.total);

// 6. Network diameter (BFS longest shortest path)
function bfs(startId) {
  const visited = new Set([startId]);
  const queue = [[startId, 0]];
  let maxDist = 0;
  while (queue.length > 0) {
    const [nodeId, dist] = queue.shift();
    maxDist = Math.max(maxDist, dist);
    for (const e of (outgoing[nodeId] || [])) {
      const t = typeof e.target === 'string' ? e.target : e.target.id;
      if (!visited.has(t)) { visited.add(t); queue.push([t, dist + 1]); }
    }
    for (const e of (incoming[nodeId] || [])) {
      const s = typeof e.source === 'string' ? e.source : e.source.id;
      if (!visited.has(s)) { visited.add(s); queue.push([s, dist + 1]); }
    }
  }
  return { maxDist, reachable: visited.size };
}

const diameters = {};
for (const node of fileNodes) {
  diameters[node.id] = bfs(node.id);
}

// 7. Clustering coefficient (undirected triangle count)
function getNeighbors(nodeId) {
  const nbrs = new Set();
  for (const e of (outgoing[nodeId] || [])) {
    const t = typeof e.target === 'string' ? e.target : e.target.id;
    nbrs.add(t);
  }
  for (const e of (incoming[nodeId] || [])) {
    const s = typeof e.source === 'string' ? e.source : e.source.id;
    if (s !== nodeId) nbrs.add(s);
  }
  return nbrs;
}

function clusteringCoefficient(nodeId) {
  const nbrs = getNeighbors(nodeId);
  const nbrArr = [...nbrs];
  if (nbrArr.length < 2) return 0;
  let triangles = 0;
  for (let i = 0; i < nbrArr.length; i++) {
    for (let j = i + 1; j < nbrArr.length; j++) {
      const a = nbrArr[i], b = nbrArr[j];
      if ((outgoing[a] || []).some(e => (typeof e.target === 'string' ? e.target : e.target.id) === b) ||
          (incoming[a] || []).some(e => (typeof e.source === 'string' ? e.source : e.source.id) === b)) {
        triangles++;
      }
    }
  }
  return (2 * triangles) / (nbrArr.length * (nbrArr.length - 1));
}

const clustering = {};
for (const node of fileNodes) {
  clustering[node.id] = clusteringCoefficient(node.id);
}

// 8. Suggest layers based on directory + type
const suggestedLayers = [];
// Root-level documents
const rootDocs = fileNodes.filter(n => n.type === 'document' && path.dirname(n.filePath) === '.');
if (rootDocs.length > 0) {
  suggestedLayers.push({
    name: 'Root Documents',
    nodeIds: rootDocs.map(n => n.id),
    description: 'Top-level documentation files defining the brainstorming skill, process, and guides.'
  });
}
// Scripts by subtype
const scriptFiles = fileNodes.filter(n => n.type === 'file' && n.filePath.startsWith('scripts/'));
const serverFiles = scriptFiles.filter(n => n.filePath === 'scripts/server.cjs');
const clientFiles = scriptFiles.filter(n => ['scripts/frame-template.html', 'scripts/helper.js'].includes(n.filePath));
const opsFiles = scriptFiles.filter(n => ['scripts/start-server.sh', 'scripts/stop-server.sh'].includes(n.filePath));

if (serverFiles.length > 0) {
  suggestedLayers.push({
    name: 'Server',
    nodeIds: serverFiles.map(n => n.id),
    description: 'Node.js backend providing HTTP serving, WebSocket session management, file watching, and browser automation.'
  });
}
if (clientFiles.length > 0) {
  suggestedLayers.push({
    name: 'Browser Client',
    nodeIds: clientFiles.map(n => n.id),
    description: 'Client-side HTML template, CSS theming, and WebSocket-based interaction logic for the visual companion.'
  });
}
if (opsFiles.length > 0) {
  suggestedLayers.push({
    name: 'Operations',
    nodeIds: opsFiles.map(n => n.id),
    description: 'Shell scripts for starting, stopping, and managing the brainstorm server lifecycle.'
  });
}

const result = {
  analysisType: 'architecture-layers',
  project: 'brainstorming',
  timestamp: new Date().toISOString(),
  stats: {
    totalNodes: fileNodes.length,
    totalEdges: allEdges.length,
    directories: Object.keys(dirGroups).length,
    types: Object.keys(typeGroups)
  },
  directoryGrouping: dirGroups,
  typeGrouping: typeGroups,
  edgeTypeBreakdown: Object.fromEntries(
    Object.entries(edgeTypes).map(([t, edges]) => [t, edges.length])
  ),
  connectivity: {
    mostConnected: connectivity.slice(0, 5),
    leastConnected: connectivity.slice(-3)
  },
  bfsDiameter: Object.fromEntries(
    Object.entries(diameters).map(([id, d]) => [id, d.maxDist])
  ),
  clusteringCoefficient: clustering,
  suggestedLayers
};

fs.writeFileSync(outputPath, JSON.stringify(result, null, 2) + '\n');
console.log('Analysis complete. Results written to', outputPath);
console.log('Suggested layers:');
for (const layer of suggestedLayers) {
  console.log(`  ${layer.name}: ${layer.nodeIds.length} node(s) — ${layer.description}`);
}
