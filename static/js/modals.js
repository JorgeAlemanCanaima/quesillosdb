// modals.js


function setDeleteId(id) {
    window.clientToDelete = id;
  }
  
  // Confirma la eliminación del cliente
  function confirmDelete() {
    // Realiza la acción de eliminación, como enviar una solicitud al servidor
    console.log("Cliente eliminado con ID:", window.clientToDelete);
    // Cierra el modal
    let deleteModal = bootstrap.Modal.getInstance(document.getElementById('deleteModal'));
    deleteModal.hide();
  }
  
  // Almacena los datos del cliente en el formulario de edición
  function setEditData(id, nombre, telefono, direccion, email) {
    document.getElementById('editId').value = id;
    document.getElementById('editNombre').value = nombre;
    document.getElementById('editTelefono').value = telefono;
    document.getElementById('editDireccion').value = direccion;
    document.getElementById('editEmail').value = email;
  }
  
  // Guarda los cambios de edición
  function saveEdit() {
    const id = document.getElementById('editId').value;
    const nombre = document.getElementById('editNombre').value;
    const telefono = document.getElementById('editTelefono').value;
    const direccion = document.getElementById('editDireccion').value;
    const email = document.getElementById('editEmail').value;
    
    // Realiza la acción de guardar, como enviar una solicitud al servidor
    console.log("Guardado:", { id, nombre, telefono, direccion, email });
    
    // Cierra el modal
    let editModal = bootstrap.Modal.getInstance(document.getElementById('editModal'));
    editModal.hide();


  
  // Enviar solicitud para editar cliente
  function saveEdit() {
    const id = document.getElementById('editId').value;
    const nombre = document.getElementById('editNombre').value;
    const telefono = document.getElementById('editTelefono').value;
    const direccion = document.getElementById('editDireccion').value;
    const email = document.getElementById('editEmail').value;
    
    fetch(`/clientes/editar/${id}`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/x-www-form-urlencoded',
      },
      body: new URLSearchParams({
        'nombre': nombre,
        'telefono': telefono,
        'direccion': direccion,
        'email': email
      })
    })
    .then(response => {
      if (response.ok) {
        location.reload();  // Recargar la página para ver los cambios
      } else {
        console.error("Error al editar el cliente");
      }
    })
    .catch(error => console.error("Error:", error));
  }
  
  }

 
  function saveEdit() {
    const id = document.getElementById('editId').value;
    const nombre = document.getElementById('editNombre').value;
    const telefono = document.getElementById('editTelefono').value;
    const direccion = document.getElementById('editDireccion').value;
    const email = document.getElementById('editEmail').value;
    
    fetch(`/clientes/editar/${id}`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/x-www-form-urlencoded',
      },
      body: new URLSearchParams({
        'nombre': nombre,
        'telefono': telefono,
        'direccion': direccion,
        'email': email
      })
    })
    .then(response => {
      if (response.ok) {
        console.log("Cliente editado correctamente en el servidor");
        location.reload();  // Recargar la página para ver los cambios
      } else {
        console.error("Error al editar el cliente en el servidor:", response.statusText);
      }
    })
    .catch(error => console.error("Error en la solicitud de edición:", error));
  }
  let deleteClientId = null; // Guardará el ID del cliente a eliminar

function confirmDelete(id) {
    deleteClientId = id; // Guarda el ID del cliente en una variable global
    let modal = new bootstrap.Modal(document.getElementById('confirmDeleteModal'));
    modal.show(); // Muestra el modal
}

document.getElementById("confirmDeleteButton").addEventListener("click", function () {
    if (deleteClientId) {
        fetch(`/clientes/eliminar/${deleteClientId}`, {
            method: 'DELETE',
            headers: {
                'Content-Type': 'application/json'
            }
        })
        .then(response => response.json())
        .then(data => {
            if (data.status === 'success') {
                alert("Cliente eliminado con éxito");

                // Elimina la fila de la tabla sin recargar la página
                const row = document.getElementById(`row-${deleteClientId}`);
                if (row) {
                    row.remove();
                }
            } else {
                alert("Error al eliminar el cliente");
            }
        })
        .catch(error => {
            console.error('Error al eliminar el cliente:', error);
            alert('Hubo un error al intentar eliminar el cliente');
        });

        // Cierra el modal después de eliminar
        let modal = bootstrap.Modal.getInstance(document.getElementById('confirmDeleteModal'));
        modal.hide();
    }
});
  

  