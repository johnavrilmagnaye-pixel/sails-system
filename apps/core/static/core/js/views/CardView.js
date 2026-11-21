Views.base.CardView = Vue.extend({
    LAST_ITEM_ID_KEY: null,
    CARD_TAB_KEY: null,

    ready: function () {
        this.saveLastItemId(this.itemId);
    },

    methods: {
        deleteItem: function () {
            var self = this;

            bootbox.dialog({
                message: i18n.gettext('Are you sure you want to delete ') + self.modelGenitive + '?',
                buttons: {
                    cansel: {
                        label: i18n.gettext('Cancel'),
                        className: 'btn-default'
                    },
                    danger: {
                        label: '<i class="fa fa-trash-o"></i> ' + i18n.gettext('Delete'),
                        className: 'btn-danger',
                        callback: function () {
                            $.ajax({
                                url: self.itemsApiUrl + self.itemId + '/delete/',
                                type: 'POST',
                                contentType: 'application/json',
                                dataType: 'json'
                            }).done(function (response) {
                                router.go(self.redirectUrl);
                            }).fail(function (response) {
                                var msg = Utils.getResponseErrorMsg(response);
                                Utils.notify(msg || i18n.gettext('Could not delete the item'), 'error');
                            });
                        }
                    }
                }
            });
        },

        saveLastItemId: function (itemId) {
            Storage.save(this.$options.LAST_ITEM_ID_KEY, itemId);
        },

        getLastItemId: function () {
            return Storage.fetch(this.$options.LAST_ITEM_ID_KEY);
        },

        saveCardTab: function (tab) {
            Storage.save(this.$options.CARD_TAB_KEY, tab);
        },

        getCardTab: function () {
            return Storage.fetch(this.$options.CARD_TAB_KEY, 'notes');
        }
    }
});
