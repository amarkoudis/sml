// Wait for the document to be fully loaded
document.addEventListener('DOMContentLoaded', function() {
    console.log("Document loaded, initializing event creation page");
    
    // Check if jQuery is available
    if (typeof jQuery === 'undefined') {
        console.error('jQuery is not loaded');
        return;
    }

    // Initialize Select2
    $('.select2').select2({
        width: '100%'
    });

    // Initialize employees array
    window.employees = window.employees || [];
    window.shifts = window.shifts || [];

    // Load shifts data from the server
    const eventId = $("#EventID").val();
    if (eventId) {
        fetch(`/events/${eventId}/shifts`)
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    window.shifts = data.shifts;
                    console.log('Loaded shifts:', window.shifts);
                    updateShiftsTable();
                } else {
                    console.error('Error loading shifts:', data.error);
                }
            })
            .catch(error => {
                console.error('Error loading shifts:', error);
            });
    }

    // Set default times for new events
    const now = new Date();
    now.setMinutes(Math.ceil(now.getMinutes() / 15) * 15); // Round to nearest 15 minutes
    const later = new Date(now);
    later.setHours(later.getHours() + 8);

    // Format datetime for input
    function formatDatetimeLocal(date) {
        return date.toISOString().slice(0, 16);
    }

    // Set default values
    $("#EventStart").val(formatDatetimeLocal(now));
    $("#EventEnd").val(formatDatetimeLocal(later));

    // Initialize modals
    $('#addShiftModal').modal({
        show: false,
        backdrop: 'static',
        keyboard: false
    });

    $('#assignEmployeesModal').modal({
        show: false,
        backdrop: 'static',
        keyboard: false
    });

    // Add Shift button click handler
    $(document).on('click', '#addShiftBtn', function(e) {
        e.preventDefault();
        console.log("Add Shift button clicked");
        
        const eventStart = $("#EventStart").val();
        const eventEnd = $("#EventEnd").val();
        
        if (!eventStart || !eventEnd) {
            alert("Please set event start and end times first");
            return;
        }

        // Set min and max datetime for shift inputs
        $("#shiftStart").attr({
            "min": eventStart,
            "max": eventEnd
        });
        $("#shiftEnd").attr({
            "min": eventStart,
            "max": eventEnd
        });

        // Reset form and set default values
        $("#addShiftForm")[0].reset();
        $("#shiftStart").val(eventStart);
        $("#shiftEnd").val(eventEnd);
        
        // Show the modal
        $('#addShiftModal').modal('show');
    });

    // Save Shift button click handler
    $(document).on('click', '#saveShiftBtn', function() {
        const shiftName = $("#shiftName").val();
        const shiftType = $("#shiftType").val();
        const shiftStart = $("#shiftStart").val();
        const shiftEnd = $("#shiftEnd").val();
        const eventStart = $("#EventStart").val();
        const eventEnd = $("#EventEnd").val();
        const eventId = $("#EventID").val(); // Get the event ID

        console.log('Shift data:', {
            event_id: eventId,
            name: shiftName,
            type: shiftType,
            start: shiftStart,
            end: shiftEnd
        });

        if (!shiftName || !shiftStart || !shiftEnd) {
            alert("Please fill in all required fields");
            return;
        }

        if (!eventId) {
            alert("Event ID is missing. Please refresh the page and try again.");
            return;
        }

        // Validate shift times are within event times
        if (new Date(shiftStart) < new Date(eventStart)) {
            alert("Shift start time cannot be before event start time");
            return;
        }

        if (new Date(shiftEnd) > new Date(eventEnd)) {
            alert("Shift end time cannot be after event end time");
            return;
        }

        if (new Date(shiftEnd) <= new Date(shiftStart)) {
            alert("Shift end time must be after shift start time");
            return;
        }

        // Get CSRF token from the form input
        const csrfToken = $('input[name="csrf_token"]').val();
        if (!csrfToken) {
            console.error('CSRF token not found');
            alert('Security token missing. Please refresh the page and try again.');
            return;
        }

        // Send the shift data to the server
        fetch('/shifts/create', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': csrfToken
            },
            body: JSON.stringify({
                event_id: eventId,
                name: shiftName,
                type: shiftType,
                start: shiftStart,
                end: shiftEnd
            })
        })
        .then(response => {
            if (!response.ok) {
                return response.json().then(data => {
                    throw new Error(data.error || `HTTP error! status: ${response.status}`);
                });
            }
            return response.json();
        })
        .then(data => {
            if (data.success) {
                // Add the new shift to the local array
                window.shifts.push({
                    id: data.shift.id,
                    name: data.shift.name,
                    type: data.shift.type,
                    start: data.shift.start,
                    end: data.shift.end,
                    employees: []
                });
                updateShiftsTable();
                $('#addShiftModal').modal('hide');
                // Show success message
                alert('Shift created successfully');
            } else {
                alert('Error creating shift: ' + (data.error || 'Unknown error'));
            }
        })
        .catch(error => {
            console.error('Error:', error);
            alert('Error creating shift: ' + error.message);
        });
    });

    // Update shifts table
    function updateShiftsTable() {
        const tbody = $("#shiftsTableBody");
        tbody.empty();

        if (!window.shifts || window.shifts.length === 0) {
            tbody.html(`
                <tr>
                    <td colspan="7" class="text-center">No shifts added yet</td>
                </tr>
            `);
            return;
        }

        window.shifts.forEach(shift => {
            // Format employee names with their hours
            const employeeNames = shift.employees && shift.employees.length > 0 
                ? shift.employees.map(e => {
                    const emp = window.employees.find(emp => emp.employeeid === e.employeeid);
                    const name = emp ? emp.employeename : 'Unknown';
                    const hours = e.hours ? ` (${e.hours} hrs)` : '';
                    return name + hours;
                }).join(', ')
                : 'None';

            const row = $("<tr>");
            row.html(`
                <td>${shift.name}</td>
                <td>${shift.type}</td>
                <td>${new Date(shift.start).toLocaleString()}</td>
                <td>${new Date(shift.end).toLocaleString()}</td>
                <td class="employee-names">${employeeNames}</td>
                <td>${calculateShiftHours(shift)} hours</td>
                <td class="actions-cell">
                    <button type="button" class="btn btn-sm btn-primary assign-employees" data-shift-id="${shift.id}">
                        <i class="fas fa-user-plus"></i> Assign
                    </button>
                    <button type="button" class="btn btn-sm btn-info edit-shift" data-shift-id="${shift.id}">
                        <i class="fas fa-edit"></i> Edit
                    </button>
                    <button type="button" class="btn btn-sm btn-danger delete-shift" data-shift-id="${shift.id}">
                        <i class="fas fa-trash"></i> Delete
                    </button>
                </td>
            `);
            tbody.append(row);
        });

        // Add event listeners for action buttons
        $('.assign-employees').on('click', function() {
            const shiftId = $(this).data('shift-id');
            assignEmployeesToShift(shiftId);
        });

        $('.edit-shift').on('click', function() {
            const shiftId = $(this).data('shift-id');
            editShift(shiftId);
        });

        $('.delete-shift').on('click', function() {
            const shiftId = $(this).data('shift-id');
            deleteShift(shiftId);
        });
    }

    // Calculate shift hours
    function calculateShiftHours(shift) {
        const start = new Date(shift.start);
        const end = new Date(shift.end);
        const hours = (end - start) / (1000 * 60 * 60);
        return hours.toFixed(2);
    }

    // Delete shift handler
    $(document).on('click', '.delete-shift', function() {
        const shiftId = $(this).data('shift-id');
        window.shifts = window.shifts.filter(s => s.id !== shiftId);
        updateShiftsTable();
    });

    // Assign employees handler
    $(document).on('click', '.assign-employees', function() {
        const shiftId = $(this).data('shift-id');
        const shift = window.shifts.find(s => s.id === shiftId);
        
        if (!shift) {
            alert("Shift not found");
            return;
        }

        // Initialize employees array if it doesn't exist
        if (!shift.employees) {
            shift.employees = [];
        }

        $("#assignShiftId").val(shiftId);
        
        // Reset checkboxes and hours inputs
        $(".employee-checkbox").prop("checked", false);
        $(".hours-input").val("0").prop("disabled", true);

        // Show/hide hours column based on shift type
        if (shift.type === 'Partial') {
            $(".hours-input").show();
        } else {
            $(".hours-input").hide();
        }

        // Check previously assigned employees
        if (shift.employees && shift.employees.length > 0) {
            shift.employees.forEach(emp => {
                const checkbox = $(`#employee${emp.employeeid}`);
                if (checkbox.length) {
                    checkbox.prop("checked", true);
                    if (shift.type === 'Partial') {
                        checkbox.closest("tr").find(".hours-input")
                            .val(emp.hours || 0)
                            .prop("disabled", false);
                    }
                }
            });
        }

        // Render the employees list
        const tbody = $("#assignEmployeesTableBody");
        tbody.empty();

        if (!window.employees || window.employees.length === 0) {
            tbody.html(`
                <tr>
                    <td colspan="3" class="text-center">No employees available</td>
                </tr>
            `);
            return;
        }

        window.employees.forEach(emp => {
            const row = $("<tr>");
            row.html(`
                <td>
                    <div class="form-check">
                        <input type="checkbox" class="form-check-input employee-checkbox" 
                               id="employee${emp.employeeid}" value="${emp.employeeid}">
                        <label class="form-check-label" for="employee${emp.employeeid}">
                            ${emp.employeename}
                        </label>
                    </div>
                </td>
                <td>${emp.employeerolename || 'N/A'}</td>
                <td>
                    <input type="number" class="form-control hours-input" 
                           min="0" step="0.5" value="0" disabled>
                </td>
            `);
            tbody.append(row);
        });

        $("#assignEmployeesModal").modal('show');
    });

    // Save assignments handler
    $(document).on('click', '#saveAssignmentsBtn', function() {
        const shiftId = parseInt($("#assignShiftId").val());
        const shift = window.shifts.find(s => s.id === shiftId);
        
        if (!shift) {
            alert("Shift not found");
            return;
        }

        const selectedEmployees = [];
        $(".employee-checkbox:checked").each(function() {
            const employeeId = parseInt($(this).val());
            const employee = window.employees.find(e => e.employeeid === employeeId);
            
            if (employee) {
                selectedEmployees.push({
                    employeeid: employeeId,
                    employeename: employee.employeename,
                    hours: shift.type === 'Partial' ? 
                        parseFloat($(this).closest("tr").find(".hours-input").val()) || 0 : null
                });
            }
        });

        // Update the shift's employees array
        shift.employees = selectedEmployees;

        // Send the updated assignments to the server
        const csrfToken = $('input[name="csrf_token"]').val();
        if (!csrfToken) {
            console.error('CSRF token not found');
            alert('Security token missing. Please refresh the page and try again.');
            return;
        }

        fetch(`/shifts/${shiftId}/assign/${eventId}`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': csrfToken
            },
            body: JSON.stringify({
                employees: selectedEmployees
            })
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                updateShiftsTable();
                $("#assignEmployeesModal").modal('hide');
                alert('Employees assigned successfully');
            } else {
                alert('Error assigning employees: ' + (data.error || 'Unknown error'));
            }
        })
        .catch(error => {
            console.error('Error:', error);
            alert('Error assigning employees: ' + error.message);
        });
    });

    // Hours input handler for partial shifts
    $(document).on('change', '.employee-checkbox', function() {
        const hoursInput = $(this).closest("tr").find(".hours-input");
        hoursInput.prop("disabled", !this.checked);
        if (!this.checked) {
            hoursInput.val("0");
        }
    });
}); 