// Wait for the DOM to be fully loaded
document.addEventListener('DOMContentLoaded', function() {
    // Initialize Select2
    if (typeof $.fn.select2 !== 'undefined') {
        $('.select2').select2({
            theme: 'bootstrap4',
            width: '100%'
        });
    }

    // Initialize tooltips
    if (typeof $.fn.tooltip !== 'undefined') {
        $('[data-toggle="tooltip"]').tooltip();
    }

    // Initialize popovers
    if (typeof $.fn.popover !== 'undefined') {
        $('[data-toggle="popover"]').popover();
    }

    // Handle form validation
    $('form.needs-validation').on('submit', function(event) {
        if (this.checkValidity() === false) {
            event.preventDefault();
            event.stopPropagation();
        }
        $(this).addClass('was-validated');
    });

    // Auto-hide flash messages after 5 seconds
    $('.alert').delay(5000).fadeOut(500);

    // Handle modal events
    $('.modal').on('shown.bs.modal', function() {
        // Reinitialize Select2 inside modals
        if (typeof $.fn.select2 !== 'undefined') {
            $(this).find('.select2').select2({
                theme: 'bootstrap4',
                width: '100%',
                dropdownParent: $(this)
            });
        }
    });

    // Handle modal hidden event
    $('.modal').on('hidden.bs.modal', function() {
        // Reset form when modal is closed if it exists
        const form = $(this).find('form')[0];
        if (form) {
            form.reset();
            // Remove validation classes
            $(this).find('form').removeClass('was-validated');
        }
    });

    // Handle datetime inputs
    $('input[type="datetime-local"]').each(function() {
        // Set min/max attributes based on related inputs
        const $this = $(this);
        const relatedInput = $this.data('related-input');
        if (relatedInput) {
            const $related = $(relatedInput);
            if ($related.length) {
                if ($this.attr('id').includes('Start')) {
                    $related.attr('min', $this.val());
                } else if ($this.attr('id').includes('End')) {
                    $this.attr('max', $related.val());
                }
            }
        }
    });

    // Handle input changes for datetime fields
    $('input[type="datetime-local"]').on('change', function() {
        const $this = $(this);
        const relatedInput = $this.data('related-input');
        if (relatedInput) {
            const $related = $(relatedInput);
            if ($related.length) {
                if ($this.attr('id').includes('Start')) {
                    $related.attr('min', $this.val());
                } else if ($this.attr('id').includes('End')) {
                    $this.attr('max', $related.val());
                }
            }
        }
    });
}); 