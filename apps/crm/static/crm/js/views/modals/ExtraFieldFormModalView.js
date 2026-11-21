Views.modals.ExtraFieldFormModalView = Views.base.ModalView.extend({
    template: '#extra-field-form-modal-tmpl',

    mixins: [Mixins.CommonMixin, Mixins.FormMixin],
    components: {
        textEditor: Views.editors.TextEditor,
        selectEditor: Views.editors.SelectEditor,
        listEditor: Views.editors.ListEditor
    },

    props: ['modalData'], // contentType, instance
    data: function () {
        var data = _.extend({}, this.modalData),
            extraFieldTypes = Const.EXTRA_FIELD_TYPES;

        data.modalName = 'extraFieldForm';
        data.showSelectOptions = false;

        var form = {
            name: {
                name: 'name',
                label: i18n.gettext('Name'),
                editor: 'text-editor',
                defaultValue: '',
                value: '',
                error: ''
            },
            type: {
                name: 'type',
                label: i18n.gettext('Field type'),
                editor: 'select-editor',
                options: [
                    {id: extraFieldTypes.STRING, text: i18n.gettext('String')},
                    {id: extraFieldTypes.TEXT, text: i18n.gettext('Text')},
                    {id: extraFieldTypes.NUMBER, text: i18n.gettext('Number')},
                    {id: extraFieldTypes.DATE, text: i18n.gettext('Date')},
                    {id: extraFieldTypes.DATETIME, text: i18n.gettext('Date and time')},
                    {id: extraFieldTypes.SELECT, text: i18n.gettext('List')},
                    {id: extraFieldTypes.PHONES, text: i18n.gettext('Phone')},
                    {id: extraFieldTypes.EMAILS, text: i18n.gettext('Email address')}
                ],
                defaultValue: extraFieldTypes.STRING,
                value: extraFieldTypes.STRING,
                error: ''
            },
            select_options: {
                name: 'select_options',
                label: '',
                editor: 'list-editor',
                alwaysShowAddMore: true,
                defaultValue: [''],
                value: [''],
                items: [{id: 0, value: ''}],
                error: ''
            }
        };

        data.isEdit = false;
        if (!!data.instance) {
            data.isEdit = true;
            form.name.value = data.instance.name;
            form.type.disabled = true;
            form.type.value = data.instance.type;

            if (form.type.value === Const.EXTRA_FIELD_TYPES.SELECT) {
                form.select_options.value = data.instance.select_options;
                form.select_options.items = _.map(data.instance.select_options, function (option, index) {
                    return {
                        id: index,
                        value: option
                    }
                });
            }
        }

        data.form = form;

        return data;
    },

    methods: {
        submit: function () {
            var self = this,
                $submit = $(this.$els.submit),
                postData = {content_type: this.contentType},
                url = API.extraFields + (!!self.instance ? self.instance.id + '/edit/' : 'add/');

            _.forEach(this.form, function(field) {
                if (field.name !== 'select_options' || self.showSelectOptions) {
                    postData[field.name] = field.value;
                }
            });

            $submit.toggleBtnLoading(true);

            $.ajax({
                url: url,
                type: 'POST',
                data: JSON.stringify(postData),
                contentType: 'application/json',
                dataType: 'json'
            }).done(function (response) {
                $submit.toggleBtnLoading(false);
                Utils.notify(self.isEdit ? i18n.gettext('Changes saved'): i18n.gettext('New field added'));
                self.$dispatch('extraFieldSaved', self.contentType, response.extra_field, self.isEdit);
            }).fail(function (response) {
                $submit.toggleBtnLoading(false);
                self.handleFormErrors(
                    response,
                    i18n.gettext('Could not save the field. Please try again or contact support.')
                );
            });
        }
    },

    watch: {
        'form.type.value': {
            immediate: true,
            handler: function (value) {
                this.showSelectOptions = parseInt(value) === Const.EXTRA_FIELD_TYPES.SELECT;
            }
        }
    }

});
