Views.modals.PersonFormModalView = Views.base.ModalView.extend({
    template: '#person-form-modal-tmpl',

    mixins: [Mixins.CommonMixin, Mixins.FormMixin],
    components: {
        textEditor: Views.editors.TextEditor,
        textAreaEditor: Views.editors.TextAreaEditor,
        selectEditor: Views.editors.SelectEditor,
        dateEditor: Views.editors.DateEditor,
        dateTimeEditor: Views.editors.DateTimeEditor,
        listEditor: Views.editors.ListEditor
    },

    props: ['modalData'], // extraFields, instance, initialCompany, hideAddCompanyLink
    data: function () {
        var data = this.modalData;

        data.modalName = 'personForm';

        var form = {
            name: {
                name: 'name',
                label: i18n.gettext('Full name'),
                editor: 'text-editor',
                value: '',
                error: ''
            },
            company: {
                name: 'company',
                label: i18n.gettext('Company'),
                placeholder: i18n.gettext('Select a company'),
                editor: 'select-editor',
                optionType: 'company',
                options: !!data.initialCompany ? [{id: data.initialCompany.id, text: data.initialCompany.name}] : [],
                allowClear: true,
                minInput: 2,
                value: !!data.initialCompany ? data.initialCompany.id : '',
                error: ''
            },
            post: {
                name: 'post',
                label: i18n.gettext('Job title'),
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
                value: '',
                error: '',
                optionType: 'tag',
                multiple: true,
                tags: true
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
                url = API.persons + (!!self.instance ? self.instance.id + '/edit/' : 'add/');

            $submit.toggleBtnLoading(true);

            $.ajax({
                url: url,
                type: 'POST',
                data: JSON.stringify(postData),
                contentType: 'application/json',
                dataType: 'json'
            }).done(function (response) {
                $submit.toggleBtnLoading(false);
                Utils.notify(self.isEdit ? i18n.gettext('Changes saved'): i18n.gettext('New contact added'));
                self.$dispatch('personSaved', action, response.person);
            }).fail(function (response) {
                $submit.toggleBtnLoading(false);
                self.handleFormErrors(
                    response,
                    i18n.gettext('Could not save the contact. Please try again or contact support.')
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
        },
        addCompany: function () {
            this.$dispatch('addCompany');
        }
    },

    events: {
        companyAdded: function (company) {
            this.form.company.options =[{id: company.id, text: company.name}];
            this.form.company.value = company.id;
        }
    }
});
