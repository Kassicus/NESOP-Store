// CSV Table Editor for NESOP Store Admin Panel
// Provides Excel-style editing for users.csv and items.csv

(function() {
  function parseCSV(csvString) {
    const lines = csvString.trim().split('\n');
    const headers = lines[0].split(',');
    return {
      headers: headers.map(h => h.trim()),
      rows: lines.slice(1).map(line => {
        const values = line.split(',');
        return values.map(v => v.trim());
      })
    };
  }
  function toCSV(headers, rows) {
    return [headers.join(',')].concat(rows.map(row => row.join(','))).join('\n');
  }
  function createTable(headers, rows, containerId) {
    const container = document.getElementById(containerId);
    container.innerHTML = '';
    const table = document.createElement('table');
    table.className = 'csv-table-editor';
    // Hide password column for users.csv
    let displayCols = headers;
    let passwordColIdx = -1;
    if (containerId === 'users-table-editor') {
      passwordColIdx = headers.indexOf('password');
      displayCols = headers.filter(h => h !== 'password');
    }
    // Header row
    const thead = document.createElement('thead');
    const headerRow = document.createElement('tr');
    displayCols.forEach((header, i) => {
      const th = document.createElement('th');
      th.textContent = header;
      headerRow.appendChild(th);
    });
    thead.appendChild(headerRow);
    table.appendChild(thead);
    // Body rows
    const tbody = document.createElement('tbody');
    rows.forEach((row, rowIdx) => {
      const tr = document.createElement('tr');
      let displayRow = row;
      if (passwordColIdx !== -1) {
        displayRow = row.filter((cell, idx) => idx !== passwordColIdx);
      }
      displayRow.forEach((cell, colIdx) => {
        const td = document.createElement('td');
        td.contentEditable = 'true';
        td.textContent = cell;
        td.oninput = function() {
          // Map back to original row index
          let realColIdx = colIdx;
          if (passwordColIdx !== -1 && colIdx >= passwordColIdx) realColIdx++;
          rows[rowIdx][realColIdx] = td.textContent;
        };
        tr.appendChild(td);
      });
      // Row action buttons
      const tdActions = document.createElement('td');
      // Delete row
      if (rows.length > 1) {
        const delBtn = document.createElement('button');
        delBtn.textContent = '✕';
        delBtn.className = 'editor-action-btn delete';
        delBtn.title = 'Delete row';
        delBtn.onclick = function() {
          if (confirm('Delete this row?')) {
            rows.splice(rowIdx, 1);
            createTable(headers, rows, containerId);
          }
        };
        tdActions.appendChild(delBtn);
      }
      tr.appendChild(tdActions);
      tbody.appendChild(tr);
    });
    // Add row button
    if (containerId !== 'users-table-editor') {
      const trAdd = document.createElement('tr');
      for (let i = 0; i < headers.length; ++i) {
        trAdd.appendChild(document.createElement('td'));
      }
      const tdAdd = document.createElement('td');
      const addBtn = document.createElement('button');
      addBtn.textContent = '+';
      addBtn.className = 'editor-action-btn add';
      addBtn.title = 'Add row';
      addBtn.onclick = function() {
        rows.push(Array(headers.length).fill(''));
        createTable(headers, rows, containerId);
      };
      tdAdd.appendChild(addBtn);
      trAdd.appendChild(tdAdd);
      tbody.appendChild(trAdd);
    }
    table.appendChild(tbody);
    container.appendChild(table);
  }
  // Main entry point for each CSV
  window.initCSVTableEditor = function(filename, containerId, msgId) {
    fetch(`/api/csv/${filename}?username=admin`)
      .then(res => res.json())
      .then(data => {
        if (data.content) {
          const parsed = parseCSV(data.content);
          createTable(parsed.headers, parsed.rows, containerId);
          container = document.getElementById(containerId);
          container.dataset.headers = JSON.stringify(parsed.headers);
          container.dataset.rows = JSON.stringify(parsed.rows);
          document.getElementById(msgId).textContent = '';
        } else {
          document.getElementById(msgId).textContent = data.error || 'Failed to load.';
        }
      })
      .catch(() => {
        document.getElementById(msgId).textContent = 'Failed to load.';
      });
  };

  // Save handler (now global, not redefined)
  window.saveCSVTable = function(filename) {
    const containerId = filename === 'users.csv' ? 'users-table-editor' : 'items-table-editor';
    const msgId = filename === 'users.csv' ? 'users-msg' : 'items-msg';
    const container = document.getElementById(containerId);
    let headers, rows;
    // Re-parse from DOM
    const table = container.querySelector('table');
    if (!table) return;
    // Only use header columns, ignore the last th (actions)
    headers = Array.from(table.querySelectorAll('thead th')).slice(0, -1).map(th => {
      // Get only the text node, ignore button
      for (let node of th.childNodes) {
        if (node.nodeType === 3) return node.nodeValue.trim();
      }
      // Fallback: remove button text
      return th.textContent.replace('✕', '').replace('+', '').trim();
    });
    rows = Array.from(table.querySelectorAll('tbody tr')).slice(0, -1).map(tr =>
      Array.from(tr.querySelectorAll('td')).slice(0, headers.length).map(td => td.textContent.trim())
    );
    const csvContent = toCSV(headers, rows);
    fetch(`/api/csv/${filename}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ username: 'admin', content: csvContent })
    })
    .then(res => res.json())
    .then(data => {
      if (data.success) {
        document.getElementById(msgId).textContent = 'Saved!';
      } else {
        document.getElementById(msgId).textContent = data.error || 'Failed to save.';
      }
    })
    .catch(() => {
      document.getElementById(msgId).textContent = 'Failed to save.';
    });
  };
})(); 