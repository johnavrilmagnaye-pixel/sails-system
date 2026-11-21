Mixins.GridCheckboxesMixin = {
    computed: {
        showActionsBtn: function () {
            return _.any(this.items, {checked: true})
        }
    },
    ready: function () {
        var self = this;

        $(document).on('click.modal', '.export-modal .submit-btn', function (e) {
            e.preventDefault();

            var $btn = $(this),
                $form = $btn.closest('form'),
                $modal = $form.closest('.modal');

            $.ajax({
                url: API.itemsExport,
                type: 'POST',
                data: JSON.stringify({
                    model_name: self.modelName,
                    extension: $form.find('input[name="extension"]:checked').val(),
                    query: _.omit(self.filters, _.isEmpty),
                    items: $btn.data('select') === 'checked' ? self.getCheckedItems(self.items) : null
                }),
                contentType: 'application/json',
                dataType: 'json'
            }).done(function (response) {
                self.itemsExportId = response.items_export_id;
                $modal.modal('hide');
                Utils.notify(i18n.gettext('The export file is being generated. Do not reload the page.'));
                setTimeout(self.checkItemsExport, 5000);
            }).fail(function (response) {
                var msg = Utils.getResponseErrorMsg(response);
                Utils.notify(msg || i18n.gettext('Could not export data'), 'error');
            });
        });
    },
    beforeDestroy: function () {
        $(document).off('click.modal', '.export-modal .submit-btn');
    },
    methods: {
        checkItemsExport: function () {
            var self = this;

            $.getJSON(
                API.itemsExport + this.itemsExportId + '/'
            ).done(function (response) {
                if (response.is_ready) {
                    window.location.pathname = response.url;
                    return;
                }

                setTimeout(self.checkItemsExport, 5000);
            }).fail(function (response) {
                var msg = Utils.getResponseErrorMsg(response);
                Utils.notify(msg || i18n.gettext('Export error'), 'error');
            });
        },
        checkItem: function (itemId) {
            var all = true,
                item;

            if (!this.isAdmin()) {
                return;
            }

            if (itemId) {
                item =  _.find(this.items, 'id', itemId);
                item.checked = !item.checked;
            }

            _.each(this.items, function (item) {
                if (!item.checked) {
                    all = false;
                }
            });

            this.checkedAll = all;
        },
        checkAll: function () {
            var self = this;

            _.each(this.items, function (item) {
                item.checked = self.checkedAll;
            });
        },
        getCheckedItems: function (items) {
            return _.pluck(_.filter(items, {'checked': true}), 'id');
        },
        deleteItems: function () {
            var self = this,
                items = this.getCheckedItems(this.items);

            bootbox.dialog({
                message: i18n.gettext('Are you sure you want to delete the selected ') + this.modelPlural + '?',
                buttons: {
                    cansel: {
                        label: i18n.gettext('Cancel'),
                        className: 'btn-default'
                    },
                    deleteAll: {
                        label: '<i class="fa fa-trash-o"></i> ' + i18n.gettext('Delete all') + ' (' + this.paginationData.count + ')',
                        className: 'btn-danger',
                        callback: function () {
                            var postData = {
                                query: _.omit(self.filters, _.isEmpty)
                            };

                            $.ajax({
                                url: self.deleteItemsUrl,
                                type: 'POST',
                                data: JSON.stringify(postData),
                                contentType: 'application/json',
                                dataType: 'json'
                            }).done(function (response) {
                                setTimeout(function () {
                                    self.fetchData(true);
                                }, 3000);
                                Utils.notify(_.capitalize(self.modelPlural) + i18n.gettext(' are being deleted'));
                            }).fail(function (response) {
                                var msg = Utils.getResponseErrorMsg(response);
                                Utils.notify(
                                    msg || i18n.gettext('An error occurred. Please try again or contact support.'),
                                    'error'
                                );
                            });
                        }
                    },
                    deleteChecked: {
                        label: '<i class="fa fa-trash-o"></i> ' + i18n.gettext('Delete selected') + ' (' + items.length + ')',
                        className: 'btn-danger',
                        callback: function () {
                            var postData = {
                                query: _.omit(self.filters, _.isEmpty),
                                item_ids: items
                            };

                            $.ajax({
                                url: self.deleteItemsUrl,
                                type: 'POST',
                                data: JSON.stringify(postData),
                                contentType: 'application/json',
                                dataType: 'json'
                            }).done(function (response) {
                                setTimeout(function () {
                                    self.fetchData(true);
                                }, 3000);
                                Utils.notify(i18n.gettext('Selected ') + self.modelPlural + i18n.gettext(' are being deleted'));
                            }).fail(function (response) {
                                var msg = Utils.getResponseErrorMsg(response);
                                Utils.notify(
                                    msg || i18n.gettext('An error occurred. Please try again or contact support.'),
                                    'error'
                                );
                            });
                        }
                    }
                }
            });
        }
    }
};
