Views.modals.CompanyFormModalView = Views.base.ModalView.extend({
    template: '#company-form-modal-tmpl',

    mixins: [Mixins.CommonMixin, Mixins.FormMixin],
    components: {
        textEditor: Views.editors.TextEditor,
        textAreaEditor: Views.editors.TextAreaEditor,
        selectEditor: Views.editors.SelectEditor,
        dateEditor: Views.editors.DateEditor,
        dateTimeEditor: Views.editors.DateTimeEditor,
        listEditor: Views.editors.ListEditor,
        phoneListEditor: Views.editors.PhoneListEditor
    },

    props: ['modalData'], // extraFields, instance, isQuickForm
    data: function () {
        var data = this.modalData;

        data.modalName = 'companyForm';

        var form = {
            name: {
                name: 'name',
                label: i18n.gettext('Name'),
                editor: 'text-editor',
                value: '',
                error: ''
            },
            address: {
                name: 'address',
                label: i18n.gettext('Address'),
                editor: 'text-editor',
                value: '',
                error: ''
            },
            website: {
                name: 'website',
                label: i18n.gettext('Website'),
                editor: 'text-editor',
                value: '',
                error: ''
            },
            phones: {
                name: 'phones',
                label: i18n.gettext('Phone'),
                editor: 'list-editor',
                defaultValue: [''],
                value: [''],
                items: [{id: 0, value: ''}],
                error: ''
            },
            emails: {
                name: 'emails',
                label: i18n.gettext('Email address'),
                editor: 'list-editor',
                defaultValue: [''],
                value: [''],
                items: [{id: 0, value: ''}],
                error: '',
                inputType: 'email'
            }
        };

        this.initExtraFields(form, data.extraFields);

        form = _.extend(form, {
            tags: {
                name: 'tags',
                label: i18n.gettext('Tags'),
                placeholder: i18n.gettext('Select tags'),
                editor: 'select-editor',
                optionType: 'tag',
                multiple: true,
                tags: true,
                value: '',
                error: ''
            },
            responsibles: {
                name: 'responsibles',
                label: i18n.gettext('Assignees'),
                placeholder: i18n.gettext('Select assignees'),
                editor: 'select-editor',
                optionType: 'user',
                multiple: true,
                value: '',
                error: ''
            },
            details: {
                name: 'details',
                label: i18n.gettext('Additional information'),
                editor: 'text-area-editor',
                cols: 40,
                rows: 10,
                value: '',
                error: ''
            }
        });

        data.isEdit = false;
        if (!!data.instance) {
            data.isEdit = true;
            this.setInstanceValues(form, data.instance);
        }

        if (this.isGta()) {
            delete form.tags;
        }

        data.form = form;

        return data;
    },

    methods: {
        doRequest: function (action) {
            var self = this,
                $submit = $(this.$els.submit),
                postData = this.getFormData(),
                url = API.companies + (!!self.instance ? self.instance.id + '/edit/' : 'add/');

            $submit.toggleBtnLoading(true);

            $.ajax({
                url: url,
                type: 'POST',
                data: JSON.stringify(postData),
                contentType: 'application/json',
                dataType: 'json'
            }).done(function (response) {
                $submit.toggleBtnLoading(false);
                Utils.notify(self.isEdit ? i18n.gettext('Changes saved'): i18n.gettext('New company added'));
                self.$dispatch('companySaved', action, response.company);
            }).fail(function (response) {
                $submit.toggleBtnLoading(false);
                self.handleFormErrors(
                    response,
                    i18n.gettext('Could not save the company. Please try again or contact support.')
                );
            });
        },
        submit: function () {
            this.doRequest();
        },
        submitAndAddMore: function () {
            this.doRequest('addMore');
        },
        submitAndGoTo: function () {
            this.doRequest('goTo');
        }
    }
});
