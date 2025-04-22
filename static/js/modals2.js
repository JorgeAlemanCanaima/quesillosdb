// modals2.js

// Función para abrir el modal de edición y establecer los datos del producto en el formulario
function setEditData(id, nombre, precio) {
  document.getElementById('editId').value = id;  // Guarda el ID del producto
  document.getElementById('editNombre').value = nombre;
  document.getElementById('editPrecio').value = precio;
}

// Función para guardar los cambios de edición
function saveEdit() {
  const id = document.getElementById('editId').value;
  const nombre = document.getElementById('editNombre').value;
  const precio = document.getElementById('editPrecio').value;
  
  // Realiza la solicitud `POST` al servidor para actualizar el producto
  fetch(`/productos/editar/${id}`, {  // Asegúrate de que la ruta esté bien configurada en Flask
    method: 'POST',
    headers: {
      'Content-Type': 'application/x-www-form-urlencoded',
    },
    body: new URLSearchParams({
      'nombre': nombre,
      'precio': precio
    })
  })
  .then(response => {
    if (response.ok) {
      console.log("Producto editado correctamente en el servidor");
      location.reload();  // Recargar la página para ver los cambios
    } else {
      console.error("Error al editar el producto en el servidor:", response.statusText);
    }
  })
  .catch(error => console.error("Error en la solicitud de edición:", error));
}

document.addEventListener("DOMContentLoaded", () => {
  const btnIngresarProducto = document.getElementById("btnIngresarProducto");

  // Evento para el botón "Ingresar el producto!"
  btnIngresarProducto.addEventListener("click", () => {
    // Aquí podrías agregar validaciones si son necesarias
    const cantidad = document.getElementById("editcantidad").value;
    const costo = document.getElementById("editcosto").value;

    if (!cantidad || !costo) {
      alert("Por favor, complete todos los campos.");
      return;
    }

    // Simula el ingreso del producto (puedes enviar datos al servidor con fetch/axios si es necesario)
    console.log("Producto ingresado:", { cantidad, costo });

    // Mostrar el modal de confirmación
    const modalConfirmacion = new bootstrap.Modal(
      document.getElementById("modalConfirmacion")
    );
    modalConfirmacion.show();
  });
});
document.addEventListener('DOMContentLoaded', function() {
  // Configurar fecha actual por defecto
  const today = new Date().toISOString().split('T')[0];
  document.getElementById('editfecha').value = today;

  // Remover cualquier event listener previo para evitar duplicados
  const btnGuardar = document.getElementById('btnGuardarProducto');
  btnGuardar.replaceWith(btnGuardar.cloneNode(true));
  
  // Obtener la nueva referencia del botón
  const newBtnGuardar = document.getElementById('btnGuardarProducto');

  // Variable para controlar el envío
  let isSubmitting = false;

  // Manejar el clic en el botón de guardar
  newBtnGuardar.addEventListener('click', function() {
      if (isSubmitting) return;
      isSubmitting = true;
      
      // Mostrar indicador de carga (opcional)
      this.innerHTML = '<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> Guardando...';
      this.disabled = true;

      const formData = {
          proveedor: document.getElementById('editpro').value,
          producto_id: document.getElementById('editId').value,
          cantidad: document.getElementById('editcantidad').value,
          costo: document.getElementById('editcosto').value,
          fecha: document.getElementById('editfecha').value
      };

      // Validación básica
      if (!formData.proveedor || !formData.cantidad || !formData.costo || !formData.fecha) {
          alert('Por favor complete todos los campos requeridos');
          isSubmitting = false;
          this.innerHTML = 'Registrar Producto';
          this.disabled = false;
          return;
      }

      // Enviar datos al servidor
      fetch('/registrar_producto_ajax', {
          method: 'POST',
          headers: {
              'Content-Type': 'application/json',
          },
          body: JSON.stringify(formData)
      })
      .then(response => {
          if (!response.ok) {
              throw new Error('Error en la respuesta del servidor');
          }
          return response.json();
      })
      .then(data => {
          if (data.status === 'success') {
              // Cerrar el modal de registro
              const modal = bootstrap.Modal.getInstance(document.getElementById('editModal'));
              modal.hide();
              
              // Mostrar mensaje de éxito
              flashMessage('Entrada registrada correctamente', 'success');
              
              // Recargar la página para ver los cambios
              setTimeout(() => {
                  window.location.reload();
              }, 1500);
          } else {
              throw new Error(data.message || 'Error desconocido');
          }
      })
      .catch(error => {
          console.error('Error:', error);
          flashMessage('Error al registrar: ' + error.message, 'danger');
          isSubmitting = false;
          newBtnGuardar.innerHTML = 'Registrar Producto';
          newBtnGuardar.disabled = false;
      });
  });
});

// Función para mostrar mensajes flash
function flashMessage(message, category) {
  // Eliminar mensajes previos
  const oldAlerts = document.querySelectorAll('.alert-dismissible');
  oldAlerts.forEach(alert => alert.remove());
  
  const flashDiv = document.createElement('div');
  flashDiv.className = `alert alert-${category} alert-dismissible fade show`;
  flashDiv.innerHTML = `
      ${message}
      <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
  `;
  
  const container = document.querySelector('.container');
  container.prepend(flashDiv);
  
  setTimeout(() => {
      flashDiv.remove();
  }, 5000);
}
document.getElementById('btnGuardarProducto').addEventListener('click', function() {
  // Obtener los valores del formulario
  var proveedor = document.getElementById('editpro').value;

  var cantidad = document.getElementById('editcantidad').value;
  var costo = document.getElementById('editcosto').value;
  var fecha = document.getElementById('editfecha').value;
  var producto_id = document.getElementById('editId').value;  // Producto ID

  // Validar que los campos no estén vacíos
  if (!cantidad || !costo || !fecha || !producto_id || !proveedor) {
      alert('Por favor complete todos los campos');
      return;
  }

  // Enviar los datos al backend usando fetch (AJAX)
  fetch('/registrar_producto_ajax', {
      method: 'POST',
      headers: {
          'Content-Type': 'application/json'
      },
      body: JSON.stringify({
          proveedor: proveedor,
          producto_id: producto_id,
          cantidad: cantidad,
          costo: costo,
          fecha: fecha
      })
  })
  .then(response => response.json())
  .then(data => {
      if (data.status === 'success') {
          // Mostrar mensaje de éxito
          $('#modalConfirmacion').modal('show');
      } else {
          // Mostrar mensaje de error
          alert('Error al registrar el producto');
      }
  })
  .catch(error => {
      console.error('Error al registrar el producto:', error);
      alert('Hubo un error al registrar el producto');
  });
});