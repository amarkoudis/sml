// Format date to datetime-local input value
function formatDateForInput(dateString) {
    if (!dateString) return '';
    const date = new Date(dateString);
    return date.toISOString().slice(0, 16);
}

// Edit shift functionality
function editShift(shiftId) {
    // Find the shift data from the available shifts
    const shift = window.shiftsData.find(s => s.shiftid == shiftId);
    
    if (shift) {
        document.getElementById('edit_shift_id').value = shift.shiftid;
        document.getElementById('edit_shiftname').value = shift.shiftname || '';
        document.getElementById('edit_shiftstart').value = formatDateForInput(shift.shiftstart);
        document.getElementById('edit_shiftend').value = formatDateForInput(shift.shiftend);
        document.getElementById('edit_notes').value = shift.notes || '';
        
        // Show the edit modal
        new bootstrap.Modal(document.getElementById('editShiftModal')).show();
    }
}

// Delete shift functionality
function deleteShift(shiftId) {
    if (!confirm('Are you sure you want to delete this shift? This action cannot be undone.')) {
        return;
    }
    
    // Get CSRF token from meta tag
    const csrfToken = document.querySelector('meta[name="csrf-token"]').getAttribute('content');
    
    // Send delete request to server
    fetch(`/shifts/${shiftId}/delete`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': csrfToken
        },
        credentials: 'same-origin'
    })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                // Remove the shift card from the UI
                const shiftCard = document.querySelector(`[data-shift-id="${shiftId}"]`);
                if (shiftCard) {
                    shiftCard.remove();
                }
                
                // Show success message
                alert(data.message);
                
                // Reload the page to ensure all data is in sync
                window.location.reload();
            } else {
                alert(data.message || 'Error deleting shift');
            }
        })
        .catch(error => {
            console.error('Error:', error);
            alert('Error deleting shift: ' + error.message);
        });
}

// Staff assignment variables
let currentShiftId = null;
let assignedEmployees = [];

// Manage staff assignments
function manageShiftStaff(shiftId) {
    const eventId = document.querySelector('input[name="event_id"]').value;
    if (!shiftId || !eventId) {
        alert('Missing shift or event ID');
        return false;
    }
    window.location.href = `/shifts/${shiftId}/assign/${eventId}`;
    return false;
}

// Assign employee to shift
function assignEmployee(employeeId) {
    // Check if already assigned
    if (assignedEmployees.some(a => a.employeeid == employeeId)) {
        alert('This employee is already assigned to this shift.');
        return;
    }
    
    // Find employee data
    const employeeItem = document.querySelector(`.employee-item[data-employee-id="${employeeId}"]`);
    const employeeName = employeeItem.dataset.employeeName;
    const employeeRole = employeeItem.dataset.employeeRole;
    
    // Add to assigned employees array
    const newAssignment = {
        employeeid: employeeId,
        employeename: employeeName,
        employeerolename: employeeRole,
        hours: 0
    };
    
    assignedEmployees.push(newAssignment);
    
    // Add to the assigned staff container
    const assignedStaffContainer = document.getElementById('assignedStaff');
    const newEmployeeItem = document.createElement('div');
    newEmployeeItem.className = 'employee-item';
    newEmployeeItem.dataset.employeeId = employeeId;
    
    newEmployeeItem.innerHTML = `
        <div class="d-flex justify-content-between align-items-center mb-2">
            <div>
                <strong>${employeeName}</strong>
                <small class="d-block text-muted">${employeeRole || 'No role'}</small>
            </div>
            <button class="btn btn-sm btn-outline-danger remove-btn" onclick="removeAssignment(${employeeId})">
                <i class="fas fa-times"></i>
            </button>
        </div>
        <div class="mb-2">
            <label class="form-label small">Hours</label>
            <input type="number" class="form-control form-control-sm hours-input" 
                   value="0" min="0" step="0.5">
        </div>
    `;
    
    assignedStaffContainer.appendChild(newEmployeeItem);
}

// Remove assignment
function removeAssignment(employeeId) {
    // Remove from array
    assignedEmployees = assignedEmployees.filter(a => a.employeeid != employeeId);
    
    // Remove from DOM
    const employeeItem = document.querySelector(`#assignedStaff .employee-item[data-employee-id="${employeeId}"]`);
    if (employeeItem) {
        employeeItem.remove();
    }
}

// Initialize event listeners
document.addEventListener('DOMContentLoaded', function() {
    // Staff search functionality
    document.getElementById('staffSearch').addEventListener('input', function(e) {
        const searchTerm = e.target.value.toLowerCase();
        const staffItems = document.querySelectorAll('#availableStaff .employee-item');
        
        staffItems.forEach(item => {
            const name = item.dataset.employeeName.toLowerCase();
            const role = (item.dataset.employeeRole || '').toLowerCase();
            
            if (name.includes(searchTerm) || role.includes(searchTerm)) {
                item.style.display = '';
            } else {
                item.style.display = 'none';
            }
        });
    });
    
    // Clear search
    document.getElementById('clearSearch').addEventListener('click', function() {
        document.getElementById('staffSearch').value = '';
        document.querySelectorAll('#availableStaff .employee-item').forEach(item => {
            item.style.display = '';
        });
    });
    
    // Save staff assignments
    document.getElementById('saveStaffAssignments').addEventListener('click', function() {
        // Update hours from inputs
        document.querySelectorAll('#assignedStaff .employee-item').forEach(item => {
            const employeeId = item.dataset.employeeId;
            const hoursInput = item.querySelector('.hours-input');
            const hours = parseFloat(hoursInput.value) || 0;
            
            const assignment = assignedEmployees.find(a => a.employeeid == employeeId);
            if (assignment) {
                assignment.hours = hours;
            }
        });
        
        // Send updated assignments to server
        fetch('/api/save_shift_assignments', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': document.querySelector('meta[name="csrf-token"]').getAttribute('content')
            },
            credentials: 'same-origin',
            body: JSON.stringify({
                shift_id: currentShiftId,
                assignments: assignedEmployees
            })
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                // Close modal and refresh page
                document.querySelector('#staffAssignmentModal .btn-close').click();
                window.location.reload();
            } else {
                alert(data.message || 'Failed to save assignments');
            }
        })
        .catch(error => {
            console.error('Error saving assignments:', error);
            alert('Failed to save assignments. Please try again.');
        });
    });
    
    // Set default dates for new shift
    const now = new Date();
    const formattedDate = now.toISOString().slice(0, 16);
    
    const endDate = new Date(now.getTime() + (4 * 60 * 60 * 1000)); // +4 hours
    const formattedEndDate = endDate.toISOString().slice(0, 16);
    
    document.getElementById('shiftstart').value = formattedDate;
    document.getElementById('shiftend').value = formattedEndDate;
}); 