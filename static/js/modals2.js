// modals2.js

// Función para abrir el modal de edición y establecer los datos del producto en el formulario
function setEditData(productId, productName, productPrice) {
  document.getElementById('editId').value = productId;
  // Resetear el formulario
  document.getElementById('registroProductoForm').reset();
  // Restablecer la fecha actual
  const now = new Date();
  const timezoneOffset = now.getTimezoneOffset() * 60000;
  const localISOTime = (new Date(now - timezoneOffset)).toISOString().slice(0, 16);
  document.getElementById('editfecha').value = localISOTime;
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

// Inicialización cuando el DOM está cargado
document.addEventListener('DOMContentLoaded', function() {
  // Configurar fecha y hora actual por defecto
  const now = new Date();
  const timezoneOffset = now.getTimezoneOffset() * 60000;
  const localISOTime = (new Date(now - timezoneOffset)).toISOString().slice(0, 16);
  document.getElementById('editfecha').value = localISOTime;
  
  // Asignar la función setEditData al ámbito global
  window.setEditData = setEditData;

  // Obtener el modal y el formulario
  const editModal = document.getElementById('editModal');
  const form = document.getElementById('registroProductoForm');
  const submitBtn = document.getElementById('btnGuardarProducto');

  // Agregar evento para cuando el modal se cierra
  editModal.addEventListener('hidden.bs.modal', function () {
    // Resetear el formulario
    form.reset();
    // Remover clases de validación
    form.classList.remove('was-validated');
    // Restablecer la fecha actual
    document.getElementById('editfecha').value = localISOTime;
  });

  // Manejar el envío del formulario
  if (form && submitBtn) {
    submitBtn.addEventListener('click', async function(e) {
      e.preventDefault(); // Prevenir el comportamiento por defecto
      
      if (!form.checkValidity()) {
        form.classList.add('was-validated');
        return;
      }

      try {
        submitBtn.disabled = true;
        submitBtn.innerHTML = '<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> Procesando...';

        // Crear objeto con los datos del formulario
        const formData = {
          proveedor: document.getElementById('editpro').value,
          producto_id: document.getElementById('editId').value,
          cantidad: document.getElementById('editcantidad').value,
          costo: document.getElementById('editcosto').value,
          fecha: document.getElementById('editfecha').value
        };

        const response = await fetch('/registrar_producto_ajax', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'X-Requested-With': 'XMLHttpRequest'
          },
          body: JSON.stringify(formData)
        });

        if (!response.ok) {
          throw new Error('Error en la respuesta del servidor');
        }

        const result = await response.json();
        
        if (result.status === 'success') {
          // Mostrar modal de confirmación
          const confirmModal = new bootstrap.Modal(document.getElementById('modalConfirmacion'));
          confirmModal.show();
          
          // Resetear el formulario
          form.reset();
          form.classList.remove('was-validated');
          
          // Cerrar el modal de edición
          const editModal = bootstrap.Modal.getInstance(document.getElementById('editModal'));
          if (editModal) {
            editModal.hide();
          }
          
          // Recargar la página después de un breve retraso
          setTimeout(() => {
            window.location.reload();
          }, 1500);
        } else {
          throw new Error(result.message || 'Error al guardar el producto');
        }
      } catch (error) {
        console.error('Error:', error);
        flashMessage(error.message, 'danger');
      } finally {
        submitBtn.disabled = false;
        submitBtn.innerHTML = 'Registrar Producto';
      }
    });
  }
});
