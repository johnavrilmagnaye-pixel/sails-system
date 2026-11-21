Views.modals.GridConfigModalView = Views.base.ModalView.extend({
    template: '#grid-config-modal-tmpl',

    mixins: [Mixins.CommonMixin],

    props: ['modalData', 'storageKey'],  // modalData: columns, isPerson
    data: function () {
        var data = this.modalData;

        data.modalName = 'gridConfig';
        data.nameLabel = data.isPerson ? i18n.gettext('Full name') : i18n.gettext('Name');

        return data;
    },

    ready: function () {
        var self = this;

        this.columnsSortable = new Sortable(this.$els.columnsList, {
            draggable: '.form-group',
            handle: '.drag-icon-w',
            ghostClass: 'sortable-ghost',
            onEnd: function (event) {
                var column,
                    parent = event.from;

                if (event.oldIndex === event.newIndex) {
                    return;
                }

                // Let Vue move the rendered fragment after the array changes.
                // Sortable has already moved the raw DOM node at this point.
                parent.removeChild(event.item);
                if (event.oldIndex < parent.children.length) {
                    parent.insertBefore(event.item, parent.children[event.oldIndex]);
                } else {
                    parent.appendChild(event.item);
                }

                column = self.columns.splice(event.oldIndex, 1)[0];
                self.columns.splice(event.newIndex, 0, column);
            }
        });
    },

    beforeDestroy: function () {
        if (this.columnsSortable) {
            this.columnsSortable.destroy();
            this.columnsSortable = null;
        }
    },

    watch: {
        columns: {
            deep: true,
            handler: function (value) {
                Storage.save(this.storageKey || 'columns', value);
            }
        }
    }
});
