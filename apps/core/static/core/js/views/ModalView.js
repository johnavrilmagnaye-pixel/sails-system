Views.base.ModalView = Vue.extend({
    replace: true,

    ready: function () {
        var self = this,
            $modal = $(this.$els.modal),
            $title = $modal.find('.modal-header h4').first();

        this.previouslyFocusedElement = document.activeElement;
        this.modalKeydownHandler = function (event) {
            self.keepFocusInsideModal(event);
        };

        if (!$title.attr('id')) {
            $title.attr('id', 'modal-title-' + this._uid);
        }
        $modal.attr({
            role: 'dialog',
            'aria-modal': 'true',
            'aria-labelledby': $title.attr('id')
        });
        $modal.on('shown.bs.modal', function () {
            self.focusFirstControl();
            $modal.on('keydown.crmModal', self.modalKeydownHandler);
        });
        $modal.modal({
            backdrop: 'static',
            keyboard: true
        });
    },

    beforeDestroy: function () {
        var $modal = $(this.$els.modal);

        $modal.off('.crmModal').modal('hide').remove();

        if (this.previouslyFocusedElement && document.contains(this.previouslyFocusedElement)) {
            this.previouslyFocusedElement.focus();
        }

        // if this is second modal
        if (this.isQuickForm) {
            $('body').addClass('modal-open');
        }
    },

    methods: {
        getFocusableElements: function () {
            return $(this.$els.modal).find(
                'a[href], button:not([disabled]), input:not([disabled]):not([type="hidden"]), ' +
                'select:not([disabled]), textarea:not([disabled]), [tabindex]:not([tabindex="-1"])'
            ).filter(':visible');
        },
        focusFirstControl: function () {
            var $focusable = this.getFocusableElements();

            if ($focusable.length) {
                $focusable.first().focus();
            } else {
                $(this.$els.modal).attr('tabindex', '-1').focus();
            }
        },
        keepFocusInsideModal: function (event) {
            var $focusable, first, last;

            if (event.keyCode !== 9) {
                return;
            }

            $focusable = this.getFocusableElements();
            if (!$focusable.length) {
                event.preventDefault();
                return;
            }

            first = $focusable[0];
            last = $focusable[$focusable.length - 1];
            if (event.shiftKey && document.activeElement === first) {
                event.preventDefault();
                last.focus();
            } else if (!event.shiftKey && document.activeElement === last) {
                event.preventDefault();
                first.focus();
            }
        },
        cancelModal: function () {
            this.$dispatch('modalCanceled', this.modalName);
        }
    }
});
