import Chart from 'chart.js/auto';

/* Production-ready WebSocket and dashboard update script */

'use strict';

/* Configuration */
const WS_URL = 'wss://example.com/socket'; // Replace with actual WebSocket URL
const RECONNECT_INTERVAL_MS = 5000; // Initial reconnect delay
const MAX_RECONNECT_ATTEMPTS = 10;
const AUTO_REFRESH_INTERVAL_MS = 60000; // 1 minute auto-refresh

/* DOM Elements */
const cpuProgressBar = document.getElementById('cpu-progress');
const memoryProgressBar = document.getElementById('memory-progress');
const statusIndicator = document.getElementById('status-indicator');
const dataTableBody = document.getElementById('data-table-body');

/* Chart Instances */
let cpuChart;
let memoryChart;

/* WebSocket instance */
let socket;
let reconnectAttempts = 0;

/* Utility: Debounce function */
function debounce(fn, delay) {
  let timeoutId;
  return (...args) => {
    clearTimeout(timeoutId);
    timeoutId = setTimeout(() => fn.apply(this, args), delay);
  };
}

/* Update progress bar */
function updateProgressBar(barElement, value) {
  if (!barElement) return;
  const clamped = Math.max(0, Math.min(100, value));
  barElement.style.width = `${clamped}%`;
  barElement.textContent = `${clamped}%`;
}

/* Update status indicator */
function updateStatusIndicator(status) {
  if (!statusIndicator) return;
  statusIndicator.textContent = status;
  statusIndicator.className = ''; // Reset classes
  statusIndicator.classList.add('status', status.toLowerCase());
}

/* Update data table */
function updateTableRow(rowId, data) {
  const existingRow = document.getElementById(rowId);
  if (existingRow) {
    existingRow.querySelector('.cpu').textContent = `${data.cpu}%`;
    existingRow.querySelector('.memory').textContent = `${data.memory}%`;
    existingRow.querySelector('.disk').textContent = `${data.disk}%`;
  } else {
    const row = document.createElement('tr');
    row.id = rowId;
    row.innerHTML = `
      <td class="name">${data.name}</td>
      <td class="cpu">${data.cpu}%</td>
      <td class="memory">${data.memory}%</td>
      <td class="disk">${data.disk}%</td>
    `;
    dataTableBody.appendChild(row);
  }
}

/* Initialize charts */
function initCharts() {
  const cpuCtx = document.getElementById('cpu-chart').getContext('2d');
  const memoryCtx = document.getElementById('memory-chart').getContext('2d');

  cpuChart = new Chart(cpuCtx, {
    type: 'line',
    data: {
      labels: [],
      datasets: [{
        label: 'CPU Usage (%)',
        data: [],
        borderColor: 'rgba(75,192,192,1)',
        fill: false,
      }],
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      scales: {
        x: { display: true },
        y: { min: 0, max: 100 },
      },
    },
  });

  memoryChart = new Chart(memoryCtx, {
    type: 'line',
    data: {
      labels: [],
      datasets: [{
        label: 'Memory Usage (%)',
        data: [],
        borderColor: 'rgba(153,102,255,1)',
        fill: false,
      }],
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      scales: {
        x: { display: true },
        y: { min: 0, max: 100 },
      },
    },
  });
}

/* Update charts with new data */
const updateCharts = debounce((timestamp, cpu, memory) => {
  if (!cpuChart || !memoryChart) return;

  cpuChart.data.labels.push(timestamp);
  cpuChart.data.datasets[0].data.push(cpu);
  if (cpuChart.data.labels.length > 60) {
    cpuChart.data.labels.shift();
    cpuChart.data.datasets[0].data.shift();
  }
  cpuChart.update();

  memoryChart.data.labels.push(timestamp);
  memoryChart.data.datasets[0].data.push(memory);
  if (memoryChart.data.labels.length > 60) {
    memoryChart.data.labels.shift();
    memoryChart.data.datasets[0].data.shift();
  }
  memoryChart.update();
}, 500);

/* WebSocket connection logic */
function connectWebSocket() {
  socket = new WebSocket(WS_URL);

  socket.addEventListener('open', () => {
    console.log('WebSocket connected');
    reconnectAttempts = 0;
    updateStatusIndicator('Connected');
  });

  socket.addEventListener('message', (event) => {
    try {
      const payload = JSON.parse(event.data);
      const timestamp = new Date().toLocaleTimeString();

      // Update progress bars
      updateProgressBar(cpuProgressBar, payload.cpu);
      updateProgressBar(memoryProgressBar, payload.memory);

      // Update status indicator
      updateStatusIndicator(payload.status || 'OK');

      // Update table
      updateTableRow(`row-${payload.id}`, {
        name: payload.name,
        cpu: payload.cpu,
        memory: payload.memory,
        disk: payload.disk,
      });

      // Update charts
      updateCharts(timestamp, payload.cpu, payload.memory);
    } catch (err) {
      console.error('Error processing WebSocket message:', err);
    }
  });

  socket.addEventListener('error', (err) => {
    console.error('WebSocket error:', err);
    updateStatusIndicator('Error');
  });

  socket.addEventListener('close', () => {
    console.warn('WebSocket closed');
    updateStatusIndicator('Disconnected');
    attemptReconnect();
  });
}

/* Reconnect logic with exponential backoff */
function attemptReconnect() {
  if (reconnectAttempts >= MAX_RECONNECT_ATTEMPTS) {
    console.error('Max reconnect attempts reached. Giving up.');
    return;
  }
  const delay = RECONNECT_INTERVAL_MS * Math.pow(2, reconnectAttempts);
  console.log(`Attempting to reconnect in ${delay} ms`);
  setTimeout(() => {
    reconnectAttempts += 1;
    connectWebSocket();
  }, delay);
}

/* Auto-refresh: send ping or request data */
function autoRefresh() {
  if (socket && socket.readyState === WebSocket.OPEN) {
    socket.send(JSON.stringify({ type: 'ping' }));
  }
}

/* Mobile-friendly adjustments */
function adjustForMobile() {
  const isMobile = window.innerWidth <= 768;
  if (isMobile) {
    document.body.classList.add('mobile');
  } else {
    document.body.classList.remove('mobile');
  }
}

/* Initialize dashboard */
function initDashboard() {
  initCharts();
  connectWebSocket();
  setInterval(autoRefresh, AUTO_REFRESH_INTERVAL_MS);
  window.addEventListener('resize', adjustForMobile);
  adjustForMobile();
}

/* Start when DOM is ready */
document.addEventListener('DOMContentLoaded', initDashboard);