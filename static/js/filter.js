// filter.js

function filterTable() {
    const filterInput = document.getElementById('filterInput').value.toLowerCase();
    const table = document.getElementById('clientesTable');
    const rows = table.getElementsByTagName('tr');
  
    for (let i = 1; i < rows.length; i++) {  // Empieza desde 1 para omitir el encabezado
      const nameCell = rows[i].getElementsByTagName('td')[1]; // Columna de nombre
      if (nameCell) {
        const name = nameCell.textContent.toLowerCase();
        rows[i].style.display = name.includes(filterInput) ? '' : 'none';
      }
    }
  }
  

  // Función para filtrar la tabla de productos en tiempo real
function setupProductFilter() {
  const filterInput = document.getElementById('filterInput2');
  
  if(filterInput) {
      // Cambiar el evento a 'input' para que filtre mientras se escribe
      filterInput.addEventListener('input', filterProductTable);
      
      // Eliminar el botón de filtrar ya que no es necesario
      const filterButton = filterInput.nextElementSibling;
      if(filterButton && filterButton.tagName === 'BUTTON') {
          filterButton.style.display = 'none';
      }
  }
}

// Función para filtrar la tabla de productos
function filterProductTable() {
  const filterValue = this.value.toLowerCase();
  const table = document.getElementById('productable');
  const rows = table.querySelectorAll('tbody tr');
  
  rows.forEach(row => {
      const codeCell = row.querySelector('td:nth-child(1)'); // Columna de código
      const nameCell = row.querySelector('td:nth-child(2)'); // Columna de nombre
      
      if (codeCell && nameCell) {
          const codeText = codeCell.textContent.toLowerCase();
          const nameText = nameCell.textContent.toLowerCase();
          
          const matches = codeText.includes(filterValue) || 
                        nameText.includes(filterValue);
          
          row.style.display = matches ? '' : 'none';
      }
  });
}

// Ejecutar cuando el DOM esté cargado
document.addEventListener('DOMContentLoaded', setupProductFilter);

