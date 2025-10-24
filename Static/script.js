async function updateStock(medicineId) {
    // Get the form for this specific medicine
    const form = document.getElementById(`stockForm${medicineId}`);
    const formData = new FormData(form);
    
    // Show loading state
    const updateButton = form.querySelector('.btn-primary');
    const originalText = updateButton.innerHTML;
    updateButton.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Updating...';
    updateButton.disabled = true;
    
    try {
        const response = await fetch(`/update_stock/${medicineId}`, {
            method: 'POST',
            body: formData
        });
        
        const result = await response.json();
        
        if (result.success) {
            // Show success message
            alert('Stock updated successfully!');
            
            // Close modal and reload page to see changes
            const modal = bootstrap.Modal.getInstance(document.getElementById(`stockModal${medicineId}`));
            modal.hide();
            
            // Reload the page to reflect changes
            setTimeout(() => {
                location.reload();
            }, 500);
            
        } else {
            alert('Error: ' + result.error);
        }
    } catch (error) {
        console.error('Error:', error);
        alert('An error occurred while updating stock. Please try again.');
    } finally {
        // Reset button state
        updateButton.innerHTML = originalText;
        updateButton.disabled = false;
    }
}

// Alternative version if you prefer the original onsubmit approach:
function handleStockUpdate(event, medicineId) {
    event.preventDefault();
    updateStock(medicineId);
}

// Auto-hide alerts after 5 seconds
document.addEventListener('DOMContentLoaded', function() {
    setTimeout(() => {
        const alerts = document.querySelectorAll('.alert');
        alerts.forEach(alert => {
            const bsAlert = new bootstrap.Alert(alert);
            bsAlert.close();
        });
    }, 5000);
});