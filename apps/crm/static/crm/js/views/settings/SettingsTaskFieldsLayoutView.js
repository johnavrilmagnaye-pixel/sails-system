Views.settings.SettingsTaskFieldsLayoutView = Vue.extend({
    template: '#settings-task-fields-layout-tmpl',

    mixins: [Mixins.CommonMixin, Mixins.ModalsMixin],
    components: {
        extraFieldFormModal: Views.modals.ExtraFieldFormModalView
    },

    data: function () {
        return {
            extraFields: [],
            contentType: 'task',
            modals: {
                extraFieldForm: {
                    show: false,
                    data: {
                        instance: null
                    }
                }
            }
        }
    },

    route: {
        data: function (transition) {
            var self = this,
                queryParams = {content_type__model: this.contentType};

            return $.getJSON(
                API.extraFields, queryParams
            ).done(function (extraFieldsData) {
                self.extraFields = extraFieldsData;
            });
        }
    },

    methods: {
        fetchData: function () {
            var self = this,
                queryParams = {content_type__model: this.contentType};

            $.getJSON(
                API.extraFields, queryParams
            ).done(function (extraFieldsData) {
                self.extraFields = extraFieldsData;
            });
        },

        toggleExtraFieldFormModal: function (showModal, instance) {
            this.modals.extraFieldForm.show = showModal;
            this.modals.extraFieldForm.data.contentType = this.contentType;
            this.modals.extraFieldForm.data.instance = instance || null;
        },

        deleteExtraField: function (extraField) {
            var self = this;

            bootbox.dialog({
                message: i18n.gettext('The field will be deleted from all tasks. Are you sure?'),
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
                                url: API.extraFields + extraField.id + '/delete/',
                                type: 'POST',
                                contentType: 'application/json',
                                dataType: 'json'
                            }).done(function (response) {
                                self.extraFields.$remove(extraField);
                            }).fail(function (response) {
                                var msg = Utils.getResponseErrorMsg(response);
                                Utils.notify(msg || i18n.gettext('Could not delete the field. Please try again or contact support.'), 'error');
                            });
                        }
                    }
                }
            });
        },

        changeIsRequired: function (extraField) {
            $.ajax({
                url: API.extraFields + extraField.id + '/change_is_required/',
                type: 'POST',
                contentType: 'application/json',
                dataType: 'json'
            }).done(function (response) {
                Utils.notify(i18n.gettext('Changes saved'), 'success');
            }).fail(function (response) {
                var msg = Utils.getResponseErrorMsg(response);
                Utils.notify(msg || i18n.gettext('An error occurred. Please try again or contact support.'), 'error');
            });
        }
    },

    events: {
        extraFieldSaved: function () {
            this.fetchData();
            this.toggleExtraFieldFormModal(false);
        }
    }
});
